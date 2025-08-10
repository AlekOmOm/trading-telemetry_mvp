
class GracefulExit:
    """Minimal graceful exit handler"""
    
    def __init__(self, app, exit_handler):
        self.app = app
        self.exit_handler = exit_handler

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.exit_handler(exc_type, exc_val, exc_tb)