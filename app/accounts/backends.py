from django.contrib.auth.backends import ModelBackend


class CompanyEmailBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        if isinstance(username, str) and "@" in username:
            username = username.strip().lower()
        return super().authenticate(request, username=username, password=password, **kwargs)
