# ��Ʊ�м�ƽ̨���

## ����
- ���� FastAPI �Ĺ�Ʊ��̨��ˣ��ṩ�û�����ɫ��������ָ�����������
- ����ͳһʹ�� MongoDB ��Ϊ���ݴ洢���Ƴ�������� MySQL ���������ݷ��ʲ㡣
- Ĭ�ϼ��� JWT ��Ȩ����ɫ/Ȩ��У���Լ� swagger �ĵ���

## ����ջ
- FastAPI + Uvicorn
- MongoDB��Motor �첽������
- Redis / Celery����ѡ������У�
- Python-JOSE + Passlib��JWT �������ϣ��

## ��Ŀ�ṹ
```
|-- app
|   |-- __init__.py
|   |-- api
|   |   |-- __init__.py
|   |   |-- auth.py
|   |   |-- indicators.py
|   |   |-- roles.py
|   |   |-- strategies.py
|   |   +-- users.py
|   |-- config.py
|   |-- core
|   |   |-- __init__.py
|   |   |-- deps.py
|   |   +-- security.py
|   |-- db
|   |   |-- __init__.py
|   |   |-- database.py
|   |   +-- database_manager.py
|   |-- example
|   |   |-- __init__.py
|   |   |-- DATABASE_MODULE_GUIDE.md
|   |   +-- database_usage_examples.py
|   |-- main.py
|   |-- models
|   |   |-- __init__.py
|   |   |-- portfolio.py
|   |   |-- role.py
|   |   |-- strategy.py
|   |   +-- user.py
|   |-- services
|   |   |-- __init__.py
|   |   |-- role_service.py
|   |   |-- strategy_service.py
|   |   +-- user_service.py
|   +-- utils
|       |-- __init__.py
|       |-- data_sources.py
|       +-- swagger_config.py
|-- scripts
|   |-- init_admin.py
|   +-- init_roles.py
|-- env.example
|-- requirements.txt
|-- run.py / start.{bat,sh}
|-- docker-compose.yml / Dockerfile
|-- SWAGGER_GUIDE.md / SWAGGER_INTEGRATION_SUMMARY.md
|-- test_api.py / test_swagger*.py
|-- uvicorn_config.py
```

> Ŀ¼�б����� `stock-system/` ��Ϊ��������Ŀ�����ĵ��۽��� `app/` ������

## �ؼ�����
- �û����ɫ��֧�ֽ�ɫ/Ȩ�޶�̬���䣬�ṩ��ɫ��Ȩ�� API��
- ���Թ����������Դ��������¡�������ȡ�����ġ�
- ָ���ѯ������ָ��ӿ�ʾ����
- ϵͳ��أ���·���� `/health` ����ʵʱ���ݿ⽡��״̬��

## ��װ������
1. ��װ����
   ```bash
   pip install -r requirements.txt
   ```
2. ���û�������
   ```bash
   cp env.example .env
   # ���ݲ��𻷾����� MongoDB / JWT / ����������Դ����
   ```
3. ��ʼ���������ݣ���ѡ��
   ```bash
   python scripts/init_roles.py
   python scripts/init_admin.py  # Ĭ���˺ţ�admin / admin123
   ```
4. ��������
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```
   ��ʹ���ṩ�� `run.py` / `start.sh` / `start.bat`��

## ����ʱ����
- Swagger �ĵ���`/docs`
- ReDoc �ĵ���`/redoc`
- OpenAPI JSON��`/openapi.json`
- ������飺`/health`

## Ĭ���˺�
- �û�����`admin`
- ���룺`admin123`
- Ȩ�ޣ�Ĭ�Ϸ��� `admin` ��ɫ����������������ʱ�޸ġ�

## ������ʾ
- ���� MongoDB ����ͨ�� `DatabaseManager` ͳһ����FastAPI `lifespan` ���Զ�������/�˳�ʱ������ر����ӡ�
- `app/example/database_usage_examples.py` ��ʾ����С�������ݿ���÷�ʽ��
- `python -m compileall app` �ɿ��ټ���﷨��

## ������չ
- ����Ҫ�����������ݿ⣬���� `app/db/database.py` ����չ�µ������߼���
- ��Ҫ���ɸ���������л򻺴棬�ɲο� `Celery` / `Redis` ������á�
