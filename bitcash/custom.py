from django.contrib import admin


class ReadOnlyModelAdmin(admin.ModelAdmin):

    """
    Hackey way to do read only admin model

    For non superusers:
      - Disable adding and deleting
      - Mark all fields as read

    Inspired by:
      - http://stackoverflow.com/a/10368029/1754586
      - http://stackoverflow.com/a/8265829/1754586

    Note that this is not bulletproof
    """

    def has_add_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

    def get_readonly_fields(self, request, obj=None):
        if request.user.is_superuser:
            return self.readonly_fields
        #get all fields as readonly
        fields = self.model._meta.get_all_field_names()
        return fields
