"""empty message

Revision ID: 25dbce6457df
Revises: 9c4b01f44d52
Create Date: 2019-10-01 00:13:48.570875

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '25dbce6457df'
down_revision = '9c4b01f44d52'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('projectLeaders',
    sa.Column('userId', sa.Integer(), nullable=False),
    sa.Column('projectId', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['projectId'], ['project.id'], ),
    sa.ForeignKeyConstraint(['userId'], ['user.id'], ),
    sa.PrimaryKeyConstraint('userId', 'projectId')
    )
    op.create_table('projectWorkers',
    sa.Column('userId', sa.Integer(), nullable=False),
    sa.Column('projectId', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['projectId'], ['project.id'], ),
    sa.ForeignKeyConstraint(['userId'], ['user.id'], ),
    sa.PrimaryKeyConstraint('userId', 'projectId')
    )
    op.create_table('project_job',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('projectId', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=50), nullable=False),
    sa.Column('description', sa.Text(), nullable=False),
    sa.Column('dateStart', sa.DateTime(), nullable=False),
    sa.Column('dateEnd', sa.DateTime(), nullable=False),
    sa.Column('estimatedTime', sa.Float(), nullable=False),
    sa.Column('workerUserId', sa.Integer(), nullable=False),
    sa.Column('parentJobId', sa.Integer(), nullable=True),
    sa.Column('creatorUserId', sa.Integer(), nullable=False),
    sa.Column('createTime', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['creatorUserId'], ['user.id'], ),
    sa.ForeignKeyConstraint(['projectId'], ['project.id'], ),
    sa.ForeignKeyConstraint(['workerUserId'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    op.drop_table('projectleaders')
    op.drop_table('projectworkers')
    op.create_foreign_key(None, 'project', 'user', ['creatorUserId'], ['id'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'project', type_='foreignkey')
    op.create_table('projectworkers',
    sa.Column('userId', mysql.INTEGER(display_width=11), autoincrement=False, nullable=False),
    sa.Column('projectId', mysql.INTEGER(display_width=11), autoincrement=False, nullable=False),
    sa.PrimaryKeyConstraint('userId', 'projectId'),
    mysql_default_charset='utf8',
    mysql_engine='MyISAM'
    )
    op.create_table('projectleaders',
    sa.Column('userId', mysql.INTEGER(display_width=11), autoincrement=False, nullable=False),
    sa.Column('projectId', mysql.INTEGER(display_width=11), autoincrement=False, nullable=False),
    sa.PrimaryKeyConstraint('userId', 'projectId'),
    mysql_default_charset='utf8',
    mysql_engine='MyISAM'
    )
    op.drop_table('project_job')
    op.drop_table('projectWorkers')
    op.drop_table('projectLeaders')
    # ### end Alembic commands ###
