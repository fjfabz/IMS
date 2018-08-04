from ..file_base_manager import file_base_manager

def test_scan_file():
    f = file_base_manager()
    f.scan_file('test/scan_test_file.py')
    info = f.file_info('test/scan_test_file.py')

    # 测试内容
    # 类数
    assert len(info['classes']) == 3
    # 方法数
    assert len(info['methods']) == 9
    for c in info['classes']:
        if c.name == 'layer_0_class':
            # 层级
            assert c.layer == 0
            # 文件位置
            assert c.begin == 10
            assert c.end == 33
            # 子方法
            assert len(c.inner_methods) == 5
            # 子类
            assert len(c.inner_classes) == 1
            assert c.inner_classes[0].layer == 1
            # 名称解析
            methods = ['__init__', 'begin_at', 'end_at', 'add_content', 'to_json']
            for i in range(len(c.inner_methods)):
                assert c.inner_methods[i].name == methods[i]
        if c.name == 'multilayer_class':
            # 子方法数
            assert len(c.inner_methods) == 1
            # 方法嵌套
            assert len(c.inner_methods[0].inner_methods) == 1
            assert c.inner_methods[0].inner_methods[0].layer == 2
            assert c.inner_methods[0].inner_methods[0].belonging == c.inner_methods[0]