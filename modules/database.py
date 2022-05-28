from tortoise.models import Model
from tortoise import fields
from tortoise import Tortoise


class Settings(Model):
    id = fields.IntField(pk=True)
    welcomeChannelId = fields.IntField()

    def __str__(self):
        return self.id


async def init():
    # Here we create a SQLite DB using file "db.sqlite3"
    #  also specify the app name of "models"
    #  which contain models from "app.models"
    await Tortoise.init(
        db_url='sqlite://database.db',
        modules={'models': ['Settings.models']}
    )
    # Generate the schema
    await Tortoise.generate_schemas()


