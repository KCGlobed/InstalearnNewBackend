from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from users.models import *
from rolepermissions import roles
from mini_lms.roles import *
from django.db import connection

class Command(BaseCommand):
    help = 'Save Roles & Permission In DB for Admin Panel Management'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Command started successfully!'))

        try:

            def get_all_postgres_table_names():
                try:
                    # 1. Get the list of all table names from the connection's schema editor
                    table_names = connection.introspection.table_names()

                    # 2. Optionally, filter out internal Django tables (starting with 'django_')
                    # This step depends on whether you want ALL tables or just your app's tables.
                    user_tables = [name for name in table_names if not name.startswith('django_') and '_historical' not in name]
                    
                    return user_tables
                    
                except Exception as e:
                    print(f"An error occurred: {e}")
                    return []
                
            def reset_sequence_for_table(table_name):
                sequence_name = f"{table_name}_id_seq"
                sql_query = f"SELECT setval('{sequence_name}', (SELECT MAX(id) FROM {table_name}), true);"
                with connection.cursor() as cursor:
                    try:
                        cursor.execute(sql_query)
                        print(f"Successfully reset sequence for table: {table_name}")
                    except Exception as e:
                        print(f"Error resetting sequence for {table_name}: {e}")
            

            all_tables = get_all_postgres_table_names()
            for table_to_fix in all_tables:
                reset_sequence_for_table(table_to_fix)

           
            self.stdout.write(self.style.SUCCESS('Command finished successfully!'))

        except Exception as e:
            raise CommandError(f'An error occurred: {e}')
