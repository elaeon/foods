from django.contrib.sitemaps import Sitemap
from news.models import News

class NewsSitemap(Sitemap):
    changefreq = "week"
    priority = 0.5

    def items(self):
        return News.objects.all()

    def lastmod(self, obj):
        return obj.date_pub
