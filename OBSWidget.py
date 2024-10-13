import asyncio
import sys
import signal
import traceback

# Use the same Python executable that is running this script
python_executable = sys.executable

async def run_player_status():
    print("Starting playerStatus.py...")
    process = await asyncio.create_subprocess_exec(
        python_executable, 'playerStatus.py',
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    async def read_stream(stream, callback):
        try:
            while True:
                line = await stream.readline()
                if line:
                    callback(line.decode('utf-8'))
                else:
                    break
        except asyncio.CancelledError:
            pass

    try:
        await asyncio.gather(
            read_stream(process.stdout, lambda line: print(line, end='')),
            read_stream(process.stderr, lambda line: print(line, end=''))
        )
    except asyncio.CancelledError:
        print("Player status task cancelled.")
    finally:
        await process.wait()  # Ensure process termination
        print("playerStatus.py has exited.")

        # Only terminate the process if it's still running
        if process.returncode is None:
            process.terminate()
            await process.wait()

async def run_web_app():
    print("Starting web/app.py...")
    process = await asyncio.create_subprocess_exec(
        python_executable, 'web/app.py',
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    async def read_stream(stream):
        try:
            while True:
                line = await stream.readline()
                if line:
                    decoded_line = line.decode('utf-8')
                    # Only print the line if it contains " * Running on"
                    if ' * Running on ' in decoded_line:
                        print(decoded_line, end='')
                else:
                    break
        except asyncio.CancelledError:
            print("Stream reading task cancelled.")
            pass

    try:
        await asyncio.gather(
            read_stream(process.stdout),
            read_stream(process.stderr)
        )
    except asyncio.CancelledError:
        print("Web app task cancelled.")
    finally:
        await process.wait()  # Ensure process termination
        print("web/app.py has exited.")

        # Only terminate the process if it's still running
        if process.returncode is None:
            process.terminate()
            await process.wait()

async def main():
    player_status_task = asyncio.create_task(run_player_status())
    web_app_task = asyncio.create_task(run_web_app())

    # Wait for both tasks and handle cancellation
    try:
        await asyncio.gather(player_status_task, web_app_task)
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
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    def handle_signal(sig, frame):
        print(f"Received signal {sig}, shutting down...")
        asyncio.ensure_future(shutdown(loop))

    # Register signals for clean shutdown
    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    try:
        loop.run_until_complete(main())
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
