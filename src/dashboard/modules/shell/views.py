from django.conf import settings
from django.conf.urls import url
from django.http import HttpResponse
from django.views.generic import TemplateView

from common.session import LaunchpadSession
from dashboard.mixins import ClientOnlineRequiredMixin
from dashboard.models import Client


class ShellView(ClientOnlineRequiredMixin, TemplateView):
    """
    Browse file system of the client.
    """
    template_name = 'client/module/shell/shell.html'

    def get(self, request, client_id):
        entry = Client.objects.get(client_id=client_id)
        context = {
            'client': entry
        }
        return self.render_to_response(context)

    def post(self, request, client_id):
        session = LaunchpadSession.clients[client_id]
        if 'cmd' in request.POST:
            cmd = request.POST['cmd']
            output = session.client.shell.run_shell_command(cmd, request.session.get('cd', '/'))
            return HttpResponse(self.format_command_input_echo(request, cmd) + output)
        elif 'cd' in request.POST:
            request.session['cd'] = path = request.POST['cd']
            return HttpResponse(self.format_command_input_echo(request, 'cd ' + path))
        else:
            return HttpResponse(status=400)

    def format_command_input_echo(self, request, command):
        return request.session.get('cd', '/') + ' % ' + command + '\n'


urlpatterns = [
    url(rf'^client/{settings.CLIENT_ID_REGEX}/shell$', ShellView.as_view(), name='client_shell'),
]
