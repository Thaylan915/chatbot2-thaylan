from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from Backend.app.api.permissions import IsAdminProfile as IsAdminUser

from Backend.app.documents.models import AdminLog


class AdminLogListView(APIView):
    """
    GET /api/admin-logs/
    Retorna os últimos 100 logs administrativos.
    """
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        logs = AdminLog.objects.select_related("user").all()[:100]
        data = [
            {
                "id":            log.id,
                "user":          log.user.username if log.user else "—",
                "action":        log.action,
                "resource_type": log.resource_type,
                "resource_id":   log.resource_id,
                "resource_name": log.resource_name,
                "details":       log.details,
                "timestamp":     log.timestamp.strftime("%d/%m/%Y %H:%M:%S"),
            }
            for log in logs
        ]
        return Response(data)