import async_lib
from lxml import html
from os import listdir
from time import time
from os import listdir


def trim_html(data, xpath):
    return html.fromstring(data).xpath(xpath)


async def get_chunks(data, chunk_size, pad=None):
    data = list(data)
    while len(data) % chunk_size:
        data.append(pad)
    return tuple([data[chunk_size*i:chunk_size*(i+1)] for i in range(len(data)//chunk_size)])


async def get_all_item_defs(min_id=0, max_id=31030, id_step=58,
                            name_xpath='//*[@id="main"]/article/div/div/h2',
                            def_xpath='//*[@id="main"]/article/div/div/table'):
    """
    Scrapes all items and their defenitions\attributes (except for stats) from runelocus website
    """
    item_client = async_lib.AsyncClient(main_loop)
    item_io = async_lib.AsyncRW('items/')
    base_url = 'http://www.runelocus.com/item-details/?item_id={}'
    try:
        for curr_id in range(min_id, max_id, id_step):
            url_load = [base_url.format(item_id) for item_id in range(curr_id, curr_id+id_step+1)]
            content = await item_client.request(url_load)
            content = {item_id[47:]: [trim_html(data, name_xpath), trim_html(data, def_xpath)] for item_id, data in content.items()}
            for item_id, detail_table in content.items():
                item_io.set_filepath('items/{}.itm'.format(item_id))
                try:
                    item_name = detail_table[0][0].text
                    await item_io.raw_open(mode='w')
                    await item_io.raw_write('item name: '+item_name[19:-1]+'\n')
                    for detail_element in detail_table[1][0].getiterator():
                        for idx, detail in enumerate(detail_element.getchildren()):
                            detail_text = detail.text.strip()
                            if detail_text in ('\\n', ''):
                                pass
                            else:
                                if idx == 0:
                                    await item_io.raw_write(detail_text+' ')
                                else:
                                    await item_io.raw_write(detail_text+'\n')
                    await item_io.raw_close()
                except IndexError:
                    await item_io.raw_close()
                    pass
                await item_io.raw_close()
            print('finished batch', (curr_id/id_step)+1, 'at', time())
    finally:
        item_client.close()
        await item_io.raw_close()


async def change_extensions(directory, old_extension, new_extension):
    for item in listdir(directory):
        if item.endswith(old_extension):
            filepath = '{}/{}'.format(directory, item)
            rename(filepath, filepath[:-4]+new_extension)


async def make_item_database():
    """
    Returns a dict containing all of the items and their relevant G.E. data (prices, names)
    """
    pass

async def main():
    await get_all_item_defs()

if __name__ == '__main__':
    main_loop = async_lib.asyncio.get_event_loop()
    main_loop.run_until_complete(main())
