try:
    import asyncio
    import aiohttp
    import aiofiles
    import time
    import requests
except Exception as e:
    if e is ImportError:
        print(e)
    else:
        print('Unhandled Exception:', e)
    exit()


class AsyncRW:

    def __init__(self, filepath, create_if_missing=True):
        self._fp = filepath
        self._cim = create_if_missing
        self._file = None

    async def set_filepath(self, newpath):
        """
        Sets the current filepath (self._fp) to newpath for the asynchronous file reader\writer.
        """
        self._fp = newpath

    async def set_cim(self, cim):
        self._cim = cim

    async def _w(self, data, mode):
        async with aiofiles.open(self._fp, mode) as file:
            await file.write(data)

    async def _r(self, mode, rl=False):
        while True:
            try:
                async with aiofiles.open(self._fp, mode) as file:
                    if rl:
                        return await file.readlines()
                    else:
                        return await file.read()
            except FileNotFoundError:
                if self._cim:
                    async with aiofiles.open(self._fp, 'x'):
                        continue
                else:
                    raise FileNotFoundError('could not find {}'.format(self._fp))

    async def write(self, data):
        """
        Writes data to the file that the current filepath (self._fp) points to.
        """
        await self._w(str(data), 'w')

    async def write_bin(self, data, encoding='utf-8'):
        """
        Writes binary data (encoded in encoding) to the file that the current filepath (self._fp) points to.
        """
        await self._w(str(data).encode(encoding), 'wb')

    async def append(self, data):
        """
        Appends data to the file that the current filepath (self._fp) points to.
        """
        await self._w(str(data), 'a')

    async def append_bin(self, data, encoding='utf-8'):
        """
        Appends binary data (encoded in param encoding) to the file that the current filepath (self._fp) points to.
        """
        await self._w(str(data).encode(encoding), 'ab')

    async def read(self):
        """
        Reads and returns data from the file that the current filepath (self._fp) points to.
        """
        return await self._r('r')

    async def readlines(self):
        """
        Reads and returns data from the file that the current filepath (self._fp) points to.
        """
        return await self._r('r', rl=True)

    async def read_bin(self, encoding='utf-8'):
        """
        Reads and returns data from the file that the current filepath (self._fp) points to.
        """
        return (await self._r('rb')).decode(encoding)

    async def raw_open(self, mode='r', encoding=None):
        """
        Opens the filepath located at self._fp to self.file
        """
        self._file = await aiofiles.open(self._fp, mode, encoding=encoding)

    async def raw_close(self):
        """
        Closes the current file that's open in self.file if there is one
        """
        if self._file:
            await self._file.close()
            self._file = None

    async def raw_write(self, data):
        await self._file.write(data)

    async def raw_read(self):
        return await self._file.read()

    async def raw_readlines(self):
        if self._file:
            return await self._file.readlines()


class AsyncClient:

    def __init__(self, loop: asyncio.get_event_loop):
        self.session = aiohttp.ClientSession(loop=loop)

    def close(self):
        """
        Closes the client's session
        """
        self.session.close()

    async def request(self, urls: [str, 'iterable']) -> dict:
        """
        Returns a dict {url1: response, url2: response, ... } from singular url or iterable of urls}
        """
        if type(urls) is str:
            async with self.session.get(urls) as response:
                return {urls: await response.read()}
        else:
            #responses is a set with all the response coroutines at idx [0].
            responses = await asyncio.wait([self.request(url) for url in urls])
            #coro_responses is the set of responses that we called. we reset responses to a dict to use later
            coro_responses = responses[0]
            responses = {}
            #this is where we get the result and add them to the responses dict
            for coro_response in coro_responses:
                #coro_response.result() is the dict {url: response}.
                responses.update(coro_response.result())
            return responses


async def url_test(urls):
    client = AsyncClient(main_loop)
    print('awaiting', len(urls), 'urls asynchronously')
    start = time.time()
    await client.request(urls)
    print('took ~{} seconds for asynchronous'.format(time.time()-start))
    client.close()
    print('requesting', len(urls), 'urls synchronously')
    start = time.time()
    [requests.get(url) for url in urls]
    print('took ~{} seconds for synchronous'.format(time.time()-start))


async def main():
    print('start main loop')
    with open('urls.txt', 'r') as file:
        urls = file.readlines()
    await url_test(urls)


if __name__ == '__main__':
    main_loop = asyncio.get_event_loop()
    main_loop.run_until_complete(main())
