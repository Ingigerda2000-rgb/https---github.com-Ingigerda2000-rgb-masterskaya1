from django.contrib.auth.tokens import PasswordResetTokenGenerator

class EmailConfirmationTokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, user, timestamp):
        # Используем pk как строку
        return str(user.pk) + str(timestamp) + str(user.email_confirmed)

email_confirmation_token = EmailConfirmationTokenGenerator()