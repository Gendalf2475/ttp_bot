from datetime import datetime
from sqlalchemy import select, func
from database.db import get_session
from database.models import User, Application
from config import SUPER_ADMINS

async def get_or_create_user(tg_user):
    async with get_session() as session:
        result = await session.execute(select(User).filter_by(user_id=tg_user.id))
        user = result.scalars().first()
        if not user:
            role = "none"
            if tg_user.id in SUPER_ADMINS:
                role = "admin"
            user = User(
                user_id=tg_user.id,
                username=tg_user.username or "",
                role=role
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)
        return user

async def get_user(user_id):
    async with get_session() as session:
        result = await session.execute(select(User).filter_by(user_id=user_id))
        return result.scalars().first()

async def set_user_role(user_id, role):
    async with get_session() as session:
        result = await session.execute(select(User).filter_by(user_id=user_id))
        user = result.scalars().first()
        if not user:
            user = User(user_id=user_id, role=role)
            session.add(user)
        else:
            user.role = role
        await session.commit()

async def get_user_role(user_id):
    if user_id in SUPER_ADMINS:
        return "admin"
        
    async with get_session() as session:
        result = await session.execute(select(User).filter_by(user_id=user_id))
        user = result.scalars().first()
        if not user:
            return "none"
        return user.role

async def set_pending_report(user_id, app_id_or_none):
    async with get_session() as session:
        result = await session.execute(select(User).filter_by(user_id=user_id))
        user = result.scalars().first()
        if user:
            if app_id_or_none is None:
                user.pending_report_app_id = None
                user.pending_report_step = None
                user.report_q1 = None
                user.report_q2 = None
                user.report_q3 = None
            else:
                user.pending_report_app_id = app_id_or_none
                user.pending_report_step = 1
                user.report_q1 = None
                user.report_q2 = None
                user.report_q3 = None
            await session.commit()

async def update_user_report_step(user_id, step, answer_text):
    async with get_session() as session:
        result = await session.execute(select(User).filter_by(user_id=user_id))
        user = result.scalars().first()
        if user:
            if step == 1:
                user.report_q1 = answer_text
                user.pending_report_step = 2
            elif step == 2:
                user.report_q2 = answer_text
                user.pending_report_step = 3
            elif step == 3:
                user.report_q3 = answer_text
                user.pending_report_step = 4
            await session.commit()

async def create_application(text, chat_id, topic_id, message_id):
    async with get_session() as session:
        now = datetime.utcnow().isoformat()
        app = Application(
            text=text,
            status='new',
            created_at=now,
            updated_at=now,
            chat_id=chat_id,
            topic_id=topic_id,
            message_id=message_id
        )
        session.add(app)
        await session.commit()
        await session.refresh(app)
        return app.id

async def get_application_by_message_id(message_id):
    async with get_session() as session:
        result = await session.execute(select(Application).filter_by(message_id=message_id))
        return result.scalars().first()

async def get_application(app_id):
    async with get_session() as session:
        result = await session.execute(select(Application).filter_by(id=app_id))
        return result.scalars().first()

async def update_application(app_id, **kwargs):
    async with get_session() as session:
        result = await session.execute(select(Application).filter_by(id=app_id))
        app = result.scalars().first()
        if app:
            for k, v in kwargs.items():
                setattr(app, k, v)
            app.updated_at = datetime.utcnow().isoformat()
            await session.commit()

async def get_stats_data(month_start_iso):
    async with get_session() as session:
        # New count
        res_new = await session.execute(
            select(func.count(Application.id)).filter(Application.created_at >= month_start_iso)
        )
        new_count = res_new.scalar()
        
        # Approved count
        res_approved = await session.execute(
            select(func.count(Application.id)).filter(
                Application.status == 'approved',
                Application.updated_at >= month_start_iso
            )
        )
        approved_count = res_approved.scalar()
        
        # Declined count
        res_declined = await session.execute(
            select(func.count(Application.id)).filter(
                Application.status.in_(['declined_pre', 'declined_final']),
                Application.updated_at >= month_start_iso
            )
        )
        declined_count = res_declined.scalar()
        
        # Moderator stats
        res_mod = await session.execute(
            select(
                Application.moderator_id, func.count(Application.id)
            ).filter(
                Application.taken_at != None,
                Application.taken_at >= month_start_iso
            ).group_by(Application.moderator_id).order_by(func.count(Application.id).desc())
        )
        moderator_stats = res_mod.all()
        
        return new_count, approved_count, declined_count, moderator_stats
