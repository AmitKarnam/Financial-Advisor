async def create_sse_event(data: str):
    # Split data into lines and prefix each with 'data: '
    lines = data.splitlines()
    return ''.join(f"data: {line}\n" for line in lines) + '\n\n'