"""Initial migration - Create all tables.

Generated manually for InfoFlow Platform.
Run after: alembic init alembic
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create sources table
    op.create_table(
        'sources',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('platform', sa.String(length=50), nullable=False),
        sa.Column('config', postgresql.JSONB(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('fetch_interval', sa.Integer(), nullable=True),
        sa.Column('last_fetch_at', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_sources_is_active'), 'sources', ['is_active'], unique=False)
    op.create_index(op.f('ix_sources_platform'), 'sources', ['platform'], unique=False)
    
    # Create contents table
    op.create_table(
        'contents',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('source_id', sa.Integer(), nullable=True),
        sa.Column('platform', sa.String(length=50), nullable=False),
        sa.Column('external_id', sa.String(length=255), nullable=False),
        sa.Column('title', sa.Text(), nullable=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('author', sa.String(length=255), nullable=True),
        sa.Column('author_id', sa.String(length=255), nullable=True),
        sa.Column('url', sa.Text(), nullable=True),
        sa.Column('published_at', sa.DateTime(), nullable=False),
        sa.Column('raw_metrics', postgresql.JSONB(), nullable=True),
        sa.Column('media_urls', postgresql.JSONB(), nullable=True),
        sa.Column('is_processed', sa.Boolean(), nullable=True),
        sa.Column('is_briefed', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['source_id'], ['sources.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('platform', 'external_id', name='uq_content_platform_external_id')
    )
    op.create_index(op.f('ix_contents_is_processed'), 'contents', ['is_processed'], unique=False)
    op.create_index(op.f('ix_contents_platform'), 'contents', ['platform'], unique=False)
    op.create_index(op.f('ix_contents_published_at'), 'contents', ['published_at'], unique=False)
    op.create_index(op.f('ix_contents_source_id'), 'contents', ['source_id'], unique=False)
    
    # Create scores table
    op.create_table(
        'scores',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('content_id', sa.Integer(), nullable=False),
        sa.Column('score_type', sa.String(length=20), nullable=False),
        sa.Column('score', sa.DECIMAL(5, 2), nullable=False),
        sa.Column('factors', postgresql.JSONB(), nullable=True),
        sa.Column('algorithm_version', sa.String(length=20), nullable=True),
        sa.Column('calculated_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['content_id'], ['contents.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('content_id', 'score_type', name='uq_score_content_type')
    )
    op.create_index(op.f('ix_scores_content_id'), 'scores', ['content_id'], unique=False)
    op.create_index(op.f('ix_scores_score_type'), 'scores', ['score_type'], unique=False)
    
    # Create tags table
    op.create_table(
        'tags',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=True),
        sa.Column('description', sa.String(length=500), nullable=True),
        sa.Column('color', sa.String(length=7), nullable=True),
        sa.Column('is_auto', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_index(op.f('ix_tags_category'), 'tags', ['category'], unique=False)
    
    # Create content_tags table
    op.create_table(
        'content_tags',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('content_id', sa.Integer(), nullable=False),
        sa.Column('tag_id', sa.Integer(), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('is_manual', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['content_id'], ['contents.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tag_id'], ['tags.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('content_id', 'tag_id', name='uq_content_tag')
    )
    op.create_index(op.f('ix_content_tags_content_id'), 'content_tags', ['content_id'], unique=False)
    op.create_index(op.f('ix_content_tags_is_manual'), 'content_tags', ['is_manual'], unique=False)
    op.create_index(op.f('ix_content_tags_tag_id'), 'content_tags', ['tag_id'], unique=False)
    
    # Create daily_briefs table
    op.create_table(
        'daily_briefs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('brief_date', sa.Date(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('stats', postgresql.JSONB(), nullable=True),
        sa.Column('total_contents', sa.Integer(), nullable=True),
        sa.Column('featured_ids', postgresql.JSONB(), nullable=True),
        sa.Column('heat_top_ids', postgresql.JSONB(), nullable=True),
        sa.Column('potential_ids', postgresql.JSONB(), nullable=True),
        sa.Column('markdown_content', sa.Text(), nullable=True),
        sa.Column('html_content', sa.Text(), nullable=True),
        sa.Column('telegram_sent', sa.Boolean(), nullable=True),
        sa.Column('email_sent', sa.Boolean(), nullable=True),
        sa.Column('sent_at', sa.DateTime(), nullable=True),
        sa.Column('generated_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('brief_date')
    )
    op.create_index(op.f('ix_daily_briefs_brief_date'), 'daily_briefs', ['brief_date'], unique=False)
    
    # Create fetch_logs table
    op.create_table(
        'fetch_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('source_id', sa.Integer(), nullable=True),
        sa.Column('platform', sa.String(length=50), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('ended_at', sa.DateTime(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('items_fetched', sa.Integer(), nullable=True),
        sa.Column('items_new', sa.Integer(), nullable=True),
        sa.Column('items_updated', sa.Integer(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('error_trace', sa.Text(), nullable=True),
        sa.Column('request_params', postgresql.JSONB(), nullable=True),
        sa.Column('response_meta', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['source_id'], ['sources.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_fetch_logs_source_id'), 'fetch_logs', ['source_id'], unique=False)
    op.create_index(op.f('ix_fetch_logs_status'), 'fetch_logs', ['status'], unique=False)
    
    # Insert default tags
    op.bulk_insert('tags', [
        {'name': 'AI', 'category': 'topic', 'color': '#10B981', 'is_auto': True},
        {'name': '科技', 'category': 'topic', 'color': '#3B82F6', 'is_auto': True},
        {'name': '投资', 'category': 'topic', 'color': '#F59E0B', 'is_auto': True},
        {'name': '生活', 'category': 'topic', 'color': '#EC4899', 'is_auto': True},
        {'name': '娱乐', 'category': 'topic', 'color': '#8B5CF6', 'is_auto': True},
        {'name': '设计', 'category': 'topic', 'color': '#06B6D4', 'is_auto': True},
        {'name': '正面', 'category': 'sentiment', 'color': '#22C55E', 'is_auto': True},
        {'name': '负面', 'category': 'sentiment', 'color': '#EF4444', 'is_auto': True},
        {'name': '中性', 'category': 'sentiment', 'color': '#6B7280', 'is_auto': True},
    ])


def downgrade() -> None:
    op.drop_table('fetch_logs')
    op.drop_table('daily_briefs')
    op.drop_table('content_tags')
    op.drop_table('tags')
    op.drop_table('scores')
    op.drop_table('contents')
    op.drop_table('sources')
