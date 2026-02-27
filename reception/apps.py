from django.apps import AppConfig


class ReceptionConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'reception'
    _cleanup_started = False

    def ready(self):
        from django.conf import settings
        import threading

        if self.__class__._cleanup_started:
            return
        if settings.DEBUG:
            import os
            if os.environ.get('RUN_MAIN') != 'true':
                return

        self.__class__._cleanup_started = True
        threading.Thread(target=self._cleanup_stale_state, daemon=True).start()

    def _cleanup_stale_state(self):
        """서버 재시작 시 in_progress 상태로 남은 방과 Redis 잔여 데이터를 정리"""
        import logging
        import json

        logger = logging.getLogger(__name__)

        try:
            from reception.models import Reception

            stale_receptions = Reception.objects.filter(state=Reception.State.IN_PROGRESS)
            for rec in stale_receptions:
                rec.state = Reception.State.WAITING
                rec.save()
        except Exception as e:
            logger.warning(f'Startup reception state cleanup failed: {e}')
            return

        try:
            import redis as redis_lib
            from django.conf import settings

            rc = redis_lib.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
            )

            for rec in stale_receptions:
                p_key = f'reception_{rec.id}_participants'
                raw_map = rc.hgetall(p_key)
                for uid_bytes, data_bytes in raw_map.items():
                    uid = uid_bytes.decode()
                    rc.delete(f'user_{uid}_reception')
                    detail = json.loads(data_bytes.decode())
                    detail['is_ready'] = 0
                    rc.hset(p_key, uid, json.dumps(detail))
        except Exception as e:
            logger.warning(f'Startup redis participant cleanup failed: {e}')
