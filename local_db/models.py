from django.db import models
import traceback
from modules.logging_config import get_plugin_logger
from datetime import datetime, timedelta
# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

from info import Info_SW as INFO

def get_valid_time():
    if INFO.IS_DEV:
        return (datetime.now() + timedelta(days=7)).date()
    else:
        return datetime.now().today()

class Login_User(models.Model):
    user_id = models.IntegerField(default= -1 )
    user_mailid = models.CharField(max_length= 250, default='' )
    user_성명 = models.CharField(max_length= 250, default='' )
    refresh_token = models.CharField(max_length= 250, default='', help_text='server 에서 경우에 따라서 발급함' )
    created_at = models.DateTimeField(auto_now_add=True)
    is_auto_login = models.BooleanField(default=False)

class Table_Config(models.Model):
    table_name = models.CharField(max_length= 250, default='table_name' )
    table_style = models.CharField(max_length= 250, default='' , null=True, blank=True )
    column_name = models.CharField(max_length= 250, default='columns_name' )
    display_name = models.CharField(max_length= 250, default='display_name' )
    column_type = models.CharField(max_length= 250, default='CharField' )
    column_width = models.IntegerField(default=0 )
    cell_style = models.JSONField(default={} )
    is_editable = models.BooleanField(default=True )
    is_hidden = models.BooleanField(default=False )

    header_menu = models.CharField(max_length= 250, null=True, blank=True )
    cell_menu = models.CharField(max_length= 250, null=True, blank=True )

    order = models.IntegerField(default=0 )


class ToolbarSettings(models.Model):
    font_family = models.CharField(max_length=100, default='Arial')
    font_size = models.IntegerField(default=16)
    font_bold = models.BooleanField(default=True)
    toolbar_color = models.CharField(max_length=20, default='#f6f5f4')
    toolbar_bg_color = models.CharField(max_length=20, default='#000000')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'toolbar_settings'


class Search_History(models.Model):
    appID = models.IntegerField(default= -1 )
    search_text = models.CharField(max_length= 250, default='' )
    search_date = models.DateTimeField(auto_now_add=True)
    count = models.IntegerField(default=0 )

    class Meta:
        db_table = 'search_history'

    def save(self, *args, **kwargs):
        self.count = self.count + 1
        super().save(*args, **kwargs)
