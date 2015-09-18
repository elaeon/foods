from news.models import News
from rest_framework import routers, serializers, viewsets

# Serializers define the API representation.
class NewsSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = News
        fields = ('date_pub', 'date_pub_edited', 'title', 'body')

# ViewSets define the view behavior.
class NewsViewSet(viewsets.ModelViewSet):
    queryset = News.objects.all().order_by("date_pub")
    serializer_class = NewsSerializer

# Routers provide an easy way of automatically determining the URL conf.
router = routers.DefaultRouter()
router.register(r'all', NewsViewSet)
