"""数据库连接与会话管理 — 使用 SQLite + SQLAlchemy"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.config import settings

# 创建数据库引擎
# check_same_thread=False 是 SQLite 在多线程环境下的必要配置
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False,  # 设为 True 可查看 SQL 日志
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 所有 ORM 模型的基类
Base = declarative_base()


def get_db():
    """获取数据库会话的依赖注入函数，用完自动关闭"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """初始化数据库，创建所有表"""
    # 导入所有模型，确保它们被注册到 Base.metadata
    import app.models.conversation  # noqa: F401
    import app.models.message  # noqa: F401
    import app.models.requirement  # noqa: F401
    import app.models.plan  # noqa: F401

    Base.metadata.create_all(bind=engine)
