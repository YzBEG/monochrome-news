from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from users.models import UserStat

class Command(BaseCommand):
    help = 'Обновляет статистику всех пользователей'
    
    def handle(self, *args, **options):
        users = User.objects.all()
        for user in users:
            if hasattr(user, 'stats'):
                user.stats.update_stats()
                self.stdout.write(f'Обновлена статистика для {user.username}')
            else:
                UserStat.objects.create(user=user)
                self.stdout.write(f'Создана статистика для {user.username}')
        
        self.stdout.write(self.style.SUCCESS('Статистика всех пользователей обновлена!'))