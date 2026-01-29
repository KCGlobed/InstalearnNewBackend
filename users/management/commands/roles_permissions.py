from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from users.models import *
from rolepermissions import roles
from mini_lms.roles import *

class Command(BaseCommand):
    help = 'Save Roles & Permission In DB for Admin Panel Management'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Command started successfully!'))

        try:
            with transaction.atomic():
                for role in roles.RolesManager.get_roles():
                    print(role.get_name())
                    all_permission_names = role.permission_names_list()
                    existing_permissions = RolePermissions.objects.filter(role=role.get_name(), code__in=all_permission_names).values_list('code', flat=True)
                    existing_permission_codes = set(existing_permissions)

                    permissions_to_create = []
                    for perm_code in all_permission_names:
                        if perm_code not in existing_permission_codes:
                            permissions_to_create.append(
                                RolePermissions(
                                    role=role.get_name(),
                                    code=perm_code,
                                    name=perm_code.replace('_', ' ').title(),
                                    status = False
                                )
                            )

                    # 2. Create all new permissions in a single bulk operation
                    if permissions_to_create:
                        RolePermissions.objects.bulk_create(permissions_to_create)


            self.stdout.write(self.style.SUCCESS('Command finished successfully!'))

        except Exception as e:
            raise CommandError(f'An error occurred: {e}')
