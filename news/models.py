from django.db import models

class News(models.Model):
    date_pub = models.DateField(auto_now_add=True)
    date_pub_edited = models.DateField(auto_now=True, blank=True, null=True)
    title = models.CharField(max_length=255)
    body = models.TextField()

    def get_absolute_url(self):
        from django.core.urlresolvers import reverse
        return reverse('nutr_news')

    def __unicode__(self):
        return self.title
    
