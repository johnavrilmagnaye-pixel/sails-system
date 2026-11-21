from django.contrib.auth.tokens import PasswordResetTokenGenerator


class UrlTokenGenerator(PasswordResetTokenGenerator):
    """ Generates expiring signed tokens """
    def _make_hash_value(self, data, timestamp):
        return '{}{}'.format(data, timestamp)


url_token_generator = UrlTokenGenerator()
