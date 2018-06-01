import sys
sys.path.append('../')
from DataService.models import get_session, Tables, Fields, ModuleReg

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


if __name__ == '__main__':
    init_sys_tables()