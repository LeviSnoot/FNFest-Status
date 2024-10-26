import asyncio
import sys
import signal
import traceback
import argparse

# Use the same Python executable that is running this script
python_executable = sys.executable

async def run_script(script_name, filter_output=None):
    print(f"Starting {script_name}")
    process = await asyncio.create_subprocess_exec(
        python_executable, script_name,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    async def read_stream(stream, callback):
        try:
            while True:
                line = await stream.readline()
                if line:
                    decoded_line = line.decode('utf-8')
                    if filter_output is None or filter_output in decoded_line:
                        callback(decoded_line)
                else:
                    break
        except asyncio.CancelledError:
            pass

    try:
        await asyncio.gather(
            read_stream(process.stdout, lambda line: print(f"{script_name} stdout: {line}", end='')),
            read_stream(process.stderr, lambda line: print(f"{script_name} stderr: {line}", end=''))
        )
    except asyncio.CancelledError:
        print(f"{script_name} task cancelled.")
    finally:
        await process.wait()  # Ensure process termination
        print(f"{script_name} has exited.")

        # Only terminate the process if it's still running
        if process.returncode is None:
            process.terminate()
            await process.wait()

async def main(args):
    tasks = [asyncio.create_task(run_script('playerStatus.py'))]

    if args.discord:
        tasks.append(asyncio.create_task(run_script('discordRPC.py')))
    if args.web:
        tasks.append(asyncio.create_task(run_script('web/app.py', filter_output=' * Running on ')))

    # Wait for all tasks and handle cancellation
    try:
        await asyncio.gather(*tasks)
    except asyncio.CancelledError:
        print("Main tasks canceled.")

async def shutdown(loop):
    """Shutdown tasks and the loop gracefully."""
    tasks = [task for task in asyncio.all_tasks() if task is not asyncio.current_task()]

    print("Cancelling running tasks...")
    for task in tasks:
        task.cancel()  # Request cancellation

    # Wait for all tasks to be cancelled
    print("Waiting for tasks to complete...")
    await asyncio.gather(*tasks, return_exceptions=True)
    print("All tasks completed.")

    # Shutdown async generators
    await loop.shutdown_asyncgens()

    # Shutdown the default executor to avoid warnings in Python 3.9+
    if hasattr(loop, 'shutdown_default_executor'):
        await loop.shutdown_default_executor()
    loop.stop()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run additional scripts.")
    parser.add_argument('--discord', action='store_true', help="Run Discord RPC")
    parser.add_argument('--web', action='store_true', help="Run Stream Widget")
    args = parser.parse_args()

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    def handle_signal(sig, frame):
        print(f"Received signal {sig}, shutting down...")
        asyncio.ensure_future(shutdown(loop))

    # Register signals for clean shutdown
    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    try:
        loop.run_until_complete(main(args))
    except KeyboardInterrupt:
        print("Exiting...")
    except Exception as e:
        print("Exception occurred:")
        traceback.print_exc()
    finally:
        try:
            loop.run_until_complete(shutdown(loop))
        except RuntimeError as e:
            print(f"RuntimeError during loop shutdown: {e}")
        except Exception as e:
            print(f"Exception during loop shutdown: {e}")
        finally:
            loop.close()
