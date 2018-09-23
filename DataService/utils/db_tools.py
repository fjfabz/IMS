import sys
import os
sys.path.append('../')
from DataService.models import get_session, Tables, Fields, ModuleReg
from DataService.table_manager import table_manager

def init_sys_tables():
    """
    初始化系统表Tables, Fields, Sensitivity
    :return:
    """
    session = get_session()
    r = session.execute("select TABLE_NAME from information_schema.TABLES where table_schema = 'ims'").fetchall()
    # print(r[0][0])
    added = True
    if not added:
        for i in range(len(r)):
            table_name = r[i][0]
            new_t = Tables(name=table_name, sensitivity=0)
            session.add(new_t)
            session.commit()
            f = session.execute("SELECT COLUMN_NAME FROM information_schema.columns\
                                  WHERE table_schema = 'ims' AND table_name = '{}'".format(table_name)).fetchall()
            for j in range(len(f)):
                new_f = Fields(name=f[j][0], table_id=new_t.id, sensitivity=0)
                session.add(new_f)
                session.commit()
    session.close()

def upgrade_sys_table():
    pass

def all_tables(db_name):
    """
    返回当前数据库中所有表名
    :return:
    """
    session = get_session()
    r = session.execute("select TABLE_NAME from information_schema.TABLES where table_schema = '{}'".format(db_name)).fetchall()
    session.close()
    a = []
    for i in range(len(r)):
        a.append(r[i][0])
    return a

def gene_file_pos():
    """
    生成当前Tables file_pos
    :return:
    """
    session = get_session()
    tables = session.query(Tables).all()
    t_manager = table_manager()
    for table in tables:
        if table.name in ['alembic_version']:
            continue
        cl = t_manager.get_table_info(table.name)
        if cl:
            table.file_pos = cl.to_json()
            session.commit()
        else:
            raise ValueError('{} do not match'.format(table.name))

if __name__ == '__main__':
    os.chdir('..')
    gene_file_pos()