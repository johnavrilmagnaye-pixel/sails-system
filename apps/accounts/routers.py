from rest_framework.routers import SimpleRouter

from accounts import viewsets


router = SimpleRouter()


router.register(r'intro', viewsets.IntroViewSet, 'intro')
router.register(r'users', viewsets.UsersViewSet, 'users')
