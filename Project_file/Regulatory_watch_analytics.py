import mysql.connector
from mysql.connector import Error
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import numpy as np
from matplotlib.backends.backend_pdf import PdfPages
import warnings
warnings.filterwarnings('ignore')

# Set style for better-looking plots
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")

class NewsDataAnalyzer:
    def __init__(self, mysql_config):
        """Initialize the analyzer with database configuration"""
        self.mysql_config = mysql_config
        self.df = None
        
    def connect_and_fetch_data(self):
        """Connect to database and fetch all articles data"""
        connection = None
        try:
            connection = mysql.connector.connect(**self.mysql_config)
            cursor = connection.cursor(dictionary=True)
            
            query = """
            SELECT 
                id,
                article_heading,
                article_link,
                keyword,
                source,
                published_date,
                is_sent,
                date_created,
                date_updated
            FROM articles
            ORDER BY date_created DESC
            """
            
            cursor.execute(query)
            data = cursor.fetchall()
            
            self.df = pd.DataFrame(data)
            
            if self.df.empty:
                print("No data found in database!")
                return False
            
            # Use published_date if available, otherwise use date_created
            self.df['effective_date'] = pd.to_datetime(
                self.df['published_date'].fillna(self.df['date_created'])
            )
            
            # Convert other date columns
            self.df['date_created'] = pd.to_datetime(self.df['date_created'])
            self.df['date_updated'] = pd.to_datetime(self.df['date_updated'])
            
            # Identify if article is from API or Scraping
            self.df['article_type'] = self.df['source'].apply(
                lambda x: 'API' if 'NewsAPI' in str(x) else 'Scraping'
            )
            
            # Extract date components
            self.df['date'] = self.df['effective_date'].dt.date
            self.df['week'] = self.df['effective_date'].dt.to_period('W')
            self.df['month'] = self.df['effective_date'].dt.to_period('M')
            self.df['year'] = self.df['effective_date'].dt.year
            self.df['day_name'] = self.df['effective_date'].dt.day_name()
            
            print(f"Successfully loaded {len(self.df)} articles from database")
            print(f"Date range: {self.df['effective_date'].min()} to {self.df['effective_date'].max()}")
            print(f"API articles: {len(self.df[self.df['article_type']=='API'])}")
            print(f"Scraping articles: {len(self.df[self.df['article_type']=='Scraping'])}")
            
            return True
            
        except Error as e:
            print(f"Error connecting to database: {e}")
            return False
        finally:
            if connection and connection.is_connected():
                cursor.close()
                connection.close()
    
    def plot_articles_by_source(self, save_path=None):
        """1. Count of Articles from sources"""
        plt.figure(figsize=(14, 8))
        
        source_counts = self.df['source'].value_counts().head(15)
        
        colors = plt.cm.Set3(range(len(source_counts)))
        bars = plt.barh(range(len(source_counts)), source_counts.values, color=colors)
        plt.yticks(range(len(source_counts)), source_counts.index)
        plt.xlabel('Number of Articles', fontsize=12, fontweight='bold')
        plt.ylabel('Source', fontsize=12, fontweight='bold')
        plt.title('Article Count by Source (Top 15)', fontsize=14, fontweight='bold', pad=20)
        plt.grid(axis='x', alpha=0.3)
        
        # Add value labels on bars
        for i, (bar, value) in enumerate(zip(bars, source_counts.values)):
            plt.text(value + 0.5, i, str(value), va='center', fontweight='bold')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(f"{save_path}_source_count.png", dpi=300, bbox_inches='tight')
        plt.show()
        
        print("\n=== Articles by Source ===")
        print(source_counts)
    
    def plot_articles_by_keyword(self, save_path=None):
        """2. Type of articles getting stored and their count (Based on Keywords)"""
        fig, axes = plt.subplots(1, 2, figsize=(16, 6))
        
        # Bar chart
        keyword_counts = self.df['keyword'].value_counts()
        colors = plt.cm.tab20(range(len(keyword_counts)))
        
        axes[0].barh(range(len(keyword_counts)), keyword_counts.values, color=colors)
        axes[0].set_yticks(range(len(keyword_counts)))
        axes[0].set_yticklabels(keyword_counts.index)
        axes[0].set_xlabel('Number of Articles', fontsize=11, fontweight='bold')
        axes[0].set_ylabel('Keyword', fontsize=11, fontweight='bold')
        axes[0].set_title('Article Count by Keyword', fontsize=13, fontweight='bold')
        axes[0].grid(axis='x', alpha=0.3)
        
        # Add value labels
        for i, value in enumerate(keyword_counts.values):
            axes[0].text(value + 0.3, i, str(value), va='center', fontweight='bold', fontsize=9)
        
        # Pie chart
        if len(keyword_counts) > 10:
            top_10 = keyword_counts.head(10)
            others = pd.Series({'Others': keyword_counts[10:].sum()})
            pie_data = pd.concat([top_10, others])
        else:
            pie_data = keyword_counts
        
        wedges, texts, autotexts = axes[1].pie(
            pie_data.values, 
            labels=pie_data.index,
            autopct='%1.1f%%',
            startangle=90,
            colors=plt.cm.tab20(range(len(pie_data)))
        )
        
        for text in texts:
            text.set_fontsize(9)
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
            autotext.set_fontsize(8)
        
        axes[1].set_title('Keyword Distribution', fontsize=13, fontweight='bold')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(f"{save_path}_keyword_count.png", dpi=300, bbox_inches='tight')
        plt.show()
        
        print("\n=== Articles by Keyword ===")
        print(keyword_counts)
    
    def plot_monthly_weekly_averages(self, save_path=None):
        """3. Monthly and weekly average of the news-articles (Based on Keywords)"""
        fig, axes = plt.subplots(2, 1, figsize=(16, 12))
        
        # Monthly averages by keyword
        monthly_keyword = self.df.groupby(['month', 'keyword']).size().unstack(fill_value=0)
        
        monthly_keyword.plot(kind='bar', ax=axes[0], width=0.8)
        axes[0].set_xlabel('Month', fontsize=11, fontweight='bold')
        axes[0].set_ylabel('Number of Articles', fontsize=11, fontweight='bold')
        axes[0].set_title('Monthly Article Count by Keyword', fontsize=13, fontweight='bold', pad=15)
        axes[0].legend(title='Keyword', bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=8)
        axes[0].grid(axis='y', alpha=0.3)
        axes[0].tick_params(axis='x', rotation=45)
        
        # Weekly averages by keyword (last 12 weeks)
        weekly_keyword = self.df.groupby(['week', 'keyword']).size().unstack(fill_value=0)
        weekly_keyword_recent = weekly_keyword.tail(12)
        
        weekly_keyword_recent.plot(kind='bar', ax=axes[1], width=0.8)
        axes[1].set_xlabel('Week', fontsize=11, fontweight='bold')
        axes[1].set_ylabel('Number of Articles', fontsize=11, fontweight='bold')
        axes[1].set_title('Weekly Article Count by Keyword (Last 12 Weeks)', fontsize=13, fontweight='bold', pad=15)
        axes[1].legend(title='Keyword', bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=8)
        axes[1].grid(axis='y', alpha=0.3)
        axes[1].tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(f"{save_path}_monthly_weekly_avg.png", dpi=300, bbox_inches='tight')
        plt.show()
        
        print("\n=== Monthly Keyword Statistics ===")
        print(monthly_keyword)
        print("\n=== Weekly Keyword Statistics (Last 12 weeks) ===")
        print(weekly_keyword_recent)
    
    def plot_api_keywords_analysis(self, save_path=None):
        """4. API related charts - keywords extracted from API"""
        api_df = self.df[self.df['article_type'] == 'API'].copy()
        
        if api_df.empty:
            print("No API articles found!")
            return
        
        fig, axes = plt.subplots(3, 1, figsize=(16, 14))
        
        # Daily basis
        daily_api = api_df.groupby(['date', 'keyword']).size().unstack(fill_value=0)
        daily_api_recent = daily_api.tail(30)
        
        daily_api_recent.plot(kind='line', ax=axes[0], marker='o', markersize=4, linewidth=2)
        axes[0].set_xlabel('Date', fontsize=11, fontweight='bold')
        axes[0].set_ylabel('Number of Articles', fontsize=11, fontweight='bold')
        axes[0].set_title('API Articles - Daily Count by Keyword (Last 30 Days)', fontsize=13, fontweight='bold', pad=15)
        axes[0].legend(title='Keyword', bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=8)
        axes[0].grid(True, alpha=0.3)
        axes[0].tick_params(axis='x', rotation=45)
        
        # Weekly basis
        weekly_api = api_df.groupby(['week', 'keyword']).size().unstack(fill_value=0)
        weekly_api_recent = weekly_api.tail(12)
        
        weekly_api_recent.plot(kind='bar', ax=axes[1], width=0.8)
        axes[1].set_xlabel('Week', fontsize=11, fontweight='bold')
        axes[1].set_ylabel('Number of Articles', fontsize=11, fontweight='bold')
        axes[1].set_title('API Articles - Weekly Count by Keyword (Last 12 Weeks)', fontsize=13, fontweight='bold', pad=15)
        axes[1].legend(title='Keyword', bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=8)
        axes[1].grid(axis='y', alpha=0.3)
        axes[1].tick_params(axis='x', rotation=45)
        
        # Monthly basis
        monthly_api = api_df.groupby(['month', 'keyword']).size().unstack(fill_value=0)
        
        monthly_api.plot(kind='bar', ax=axes[2], width=0.8)
        axes[2].set_xlabel('Month', fontsize=11, fontweight='bold')
        axes[2].set_ylabel('Number of Articles', fontsize=11, fontweight='bold')
        axes[2].set_title('API Articles - Monthly Count by Keyword', fontsize=13, fontweight='bold', pad=15)
        axes[2].legend(title='Keyword', bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=8)
        axes[2].grid(axis='y', alpha=0.3)
        axes[2].tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(f"{save_path}_api_keywords.png", dpi=300, bbox_inches='tight')
        plt.show()
        
        print("\n=== API Articles - Daily Keywords (Last 30 days) ===")
        print(daily_api_recent)
    
    def plot_scraping_keywords_analysis(self, save_path=None):
        """5. Scraping related charts - keywords extracted through scraping"""
        scraping_df = self.df[self.df['article_type'] == 'Scraping'].copy()
        
        if scraping_df.empty:
            print("No Scraping articles found!")
            return
        
        fig, axes = plt.subplots(3, 1, figsize=(16, 14))
        
        # Daily basis
        daily_scraping = scraping_df.groupby(['date', 'keyword']).size().unstack(fill_value=0)
        daily_scraping_recent = daily_scraping.tail(30)
        
        daily_scraping_recent.plot(kind='line', ax=axes[0], marker='s', markersize=4, linewidth=2)
        axes[0].set_xlabel('Date', fontsize=11, fontweight='bold')
        axes[0].set_ylabel('Number of Articles', fontsize=11, fontweight='bold')
        axes[0].set_title('Scraping Articles - Daily Count by Keyword (Last 30 Days)', fontsize=13, fontweight='bold', pad=15)
        axes[0].legend(title='Keyword', bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=8)
        axes[0].grid(True, alpha=0.3)
        axes[0].tick_params(axis='x', rotation=45)
        
        # Weekly basis
        weekly_scraping = scraping_df.groupby(['week', 'keyword']).size().unstack(fill_value=0)
        weekly_scraping_recent = weekly_scraping.tail(12)
        
        weekly_scraping_recent.plot(kind='bar', ax=axes[1], width=0.8)
        axes[1].set_xlabel('Week', fontsize=11, fontweight='bold')
        axes[1].set_ylabel('Number of Articles', fontsize=11, fontweight='bold')
        axes[1].set_title('Scraping Articles - Weekly Count by Keyword (Last 12 Weeks)', fontsize=13, fontweight='bold', pad=15)
        axes[1].legend(title='Keyword', bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=8)
        axes[1].grid(axis='y', alpha=0.3)
        axes[1].tick_params(axis='x', rotation=45)
        
        # Monthly basis
        monthly_scraping = scraping_df.groupby(['month', 'keyword']).size().unstack(fill_value=0)
        
        monthly_scraping.plot(kind='bar', ax=axes[2], width=0.8)
        axes[2].set_xlabel('Month', fontsize=11, fontweight='bold')
        axes[2].set_ylabel('Number of Articles', fontsize=11, fontweight='bold')
        axes[2].set_title('Scraping Articles - Monthly Count by Keyword', fontsize=13, fontweight='bold', pad=15)
        axes[2].legend(title='Keyword', bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=8)
        axes[2].grid(axis='y', alpha=0.3)
        axes[2].tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(f"{save_path}_scraping_keywords.png", dpi=300, bbox_inches='tight')
        plt.show()
        
        print("\n=== Scraping Articles - Daily Keywords (Last 30 days) ===")
        print(daily_scraping_recent)
    
    def plot_api_vs_scraping_comparison(self, save_path=None):
        """6. Comparison of count between API and Scraping articles"""
        fig, axes = plt.subplots(3, 1, figsize=(16, 14))
        
        # Daily basis
        daily_comparison = self.df.groupby(['date', 'article_type']).size().unstack(fill_value=0)
        daily_comparison_recent = daily_comparison.tail(30)
        
        daily_comparison_recent.plot(kind='line', ax=axes[0], marker='o', markersize=5, linewidth=2.5)
        axes[0].set_xlabel('Date', fontsize=11, fontweight='bold')
        axes[0].set_ylabel('Number of Articles', fontsize=11, fontweight='bold')
        axes[0].set_title('API vs Scraping - Daily Comparison (Last 30 Days)', fontsize=13, fontweight='bold', pad=15)
        axes[0].legend(title='Article Type', fontsize=10)
        axes[0].grid(True, alpha=0.3)
        axes[0].tick_params(axis='x', rotation=45)
        axes[0].fill_between(range(len(daily_comparison_recent)), 
                             daily_comparison_recent.get('API', 0), 
                             alpha=0.3, label='_nolegend_')
        axes[0].fill_between(range(len(daily_comparison_recent)), 
                             daily_comparison_recent.get('Scraping', 0), 
                             alpha=0.3, label='_nolegend_')
        
        # Weekly basis
        weekly_comparison = self.df.groupby(['week', 'article_type']).size().unstack(fill_value=0)
        weekly_comparison_recent = weekly_comparison.tail(12)
        
        x = np.arange(len(weekly_comparison_recent))
        width = 0.35
        
        api_counts = weekly_comparison_recent.get('API', pd.Series([0]*len(weekly_comparison_recent)))
        scraping_counts = weekly_comparison_recent.get('Scraping', pd.Series([0]*len(weekly_comparison_recent)))
        
        bars1 = axes[1].bar(x - width/2, api_counts, width, label='API', alpha=0.8)
        bars2 = axes[1].bar(x + width/2, scraping_counts, width, label='Scraping', alpha=0.8)
        
        axes[1].set_xlabel('Week', fontsize=11, fontweight='bold')
        axes[1].set_ylabel('Number of Articles', fontsize=11, fontweight='bold')
        axes[1].set_title('API vs Scraping - Weekly Comparison (Last 12 Weeks)', fontsize=13, fontweight='bold', pad=15)
        axes[1].set_xticks(x)
        axes[1].set_xticklabels([str(w) for w in weekly_comparison_recent.index], rotation=45)
        axes[1].legend(fontsize=10)
        axes[1].grid(axis='y', alpha=0.3)
        
        # Add value labels on bars
        for bars in [bars1, bars2]:
            for bar in bars:
                height = bar.get_height()
                if height > 0:
                    axes[1].text(bar.get_x() + bar.get_width()/2., height,
                               f'{int(height)}',
                               ha='center', va='bottom', fontsize=8, fontweight='bold')
        
        # Monthly basis
        monthly_comparison = self.df.groupby(['month', 'article_type']).size().unstack(fill_value=0)
        
        x = np.arange(len(monthly_comparison))
        width = 0.35
        
        api_counts = monthly_comparison.get('API', pd.Series([0]*len(monthly_comparison)))
        scraping_counts = monthly_comparison.get('Scraping', pd.Series([0]*len(monthly_comparison)))
        
        bars1 = axes[2].bar(x - width/2, api_counts, width, label='API', alpha=0.8)
        bars2 = axes[2].bar(x + width/2, scraping_counts, width, label='Scraping', alpha=0.8)
        
        axes[2].set_xlabel('Month', fontsize=11, fontweight='bold')
        axes[2].set_ylabel('Number of Articles', fontsize=11, fontweight='bold')
        axes[2].set_title('API vs Scraping - Monthly Comparison', fontsize=13, fontweight='bold', pad=15)
        axes[2].set_xticks(x)
        axes[2].set_xticklabels([str(m) for m in monthly_comparison.index], rotation=45)
        axes[2].legend(fontsize=10)
        axes[2].grid(axis='y', alpha=0.3)
        
        # Add value labels on bars
        for bars in [bars1, bars2]:
            for bar in bars:
                height = bar.get_height()
                if height > 0:
                    axes[2].text(bar.get_x() + bar.get_width()/2., height,
                               f'{int(height)}',
                               ha='center', va='bottom', fontsize=8, fontweight='bold')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(f"{save_path}_api_vs_scraping.png", dpi=300, bbox_inches='tight')
        plt.show()
        
        print("\n=== API vs Scraping - Summary ===")
        print(f"Total API articles: {len(self.df[self.df['article_type']=='API'])}")
        print(f"Total Scraping articles: {len(self.df[self.df['article_type']=='Scraping'])}")
        print("\n=== Monthly Comparison ===")
        print(monthly_comparison)
    
    def plot_source_wise_keyword_analysis(self, save_path=None):
        """7. Source wise count of articles and type of articles (based on keywords)"""
        
        # Get top 10 sources for better visualization
        top_sources = self.df['source'].value_counts().head(10).index
        source_filtered_df = self.df[self.df['source'].isin(top_sources)].copy()
        
        fig = plt.figure(figsize=(20, 16))
        gs = fig.add_gridspec(3, 2, hspace=0.3, wspace=0.3)
        
        # ============ DAILY BASIS ============
        # Daily - Source wise count
        ax1 = fig.add_subplot(gs[0, 0])
        daily_source = source_filtered_df.groupby(['date', 'source']).size().unstack(fill_value=0)
        daily_source_recent = daily_source.tail(30)
        
        daily_source_recent.plot(kind='line', ax=ax1, marker='o', markersize=3, linewidth=1.5, alpha=0.7)
        ax1.set_xlabel('Date', fontsize=10, fontweight='bold')
        ax1.set_ylabel('Number of Articles', fontsize=10, fontweight='bold')
        ax1.set_title('Daily Articles by Source (Last 30 Days) - Top 10 Sources', fontsize=12, fontweight='bold', pad=15)
        ax1.legend(title='Source', bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=7, ncol=1)
        ax1.grid(True, alpha=0.3)
        ax1.tick_params(axis='x', rotation=45, labelsize=8)
        
        # Daily - Keyword wise count
        ax2 = fig.add_subplot(gs[0, 1])
        daily_keyword = self.df.groupby(['date', 'keyword']).size().unstack(fill_value=0)
        daily_keyword_recent = daily_keyword.tail(30)
        
        # Plot only top 10 keywords for clarity
        top_keywords = self.df['keyword'].value_counts().head(10).index
        daily_keyword_top = daily_keyword_recent[top_keywords]
        
        daily_keyword_top.plot(kind='line', ax=ax2, marker='s', markersize=3, linewidth=1.5, alpha=0.7)
        ax2.set_xlabel('Date', fontsize=10, fontweight='bold')
        ax2.set_ylabel('Number of Articles', fontsize=10, fontweight='bold')
        ax2.set_title('Daily Articles by Keyword (Last 30 Days) - Top 10 Keywords', fontsize=12, fontweight='bold', pad=15)
        ax2.legend(title='Keyword', bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=7, ncol=1)
        ax2.grid(True, alpha=0.3)
        ax2.tick_params(axis='x', rotation=45, labelsize=8)
        
        # ============ WEEKLY BASIS ============
        # Weekly - Source wise count
        ax3 = fig.add_subplot(gs[1, 0])
        weekly_source = source_filtered_df.groupby(['week', 'source']).size().unstack(fill_value=0)
        weekly_source_recent = weekly_source.tail(12)
        
        weekly_source_recent.plot(kind='bar', ax=ax3, width=0.8, stacked=True, alpha=0.8)
        ax3.set_xlabel('Week', fontsize=10, fontweight='bold')
        ax3.set_ylabel('Number of Articles', fontsize=10, fontweight='bold')
        ax3.set_title('Weekly Articles by Source (Last 12 Weeks) - Top 10 Sources', fontsize=12, fontweight='bold', pad=15)
        ax3.legend(title='Source', bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=7)
        ax3.grid(axis='y', alpha=0.3)
        ax3.tick_params(axis='x', rotation=45, labelsize=8)
        
        # Weekly - Keyword wise count
        ax4 = fig.add_subplot(gs[1, 1])
        weekly_keyword = self.df.groupby(['week', 'keyword']).size().unstack(fill_value=0)
        weekly_keyword_recent = weekly_keyword.tail(12)
        
        # Show top 10 keywords
        weekly_keyword_top = weekly_keyword_recent[[k for k in top_keywords if k in weekly_keyword_recent.columns]]
        
        weekly_keyword_top.plot(kind='bar', ax=ax4, width=0.8, stacked=True, alpha=0.8)
        ax4.set_xlabel('Week', fontsize=10, fontweight='bold')
        ax4.set_ylabel('Number of Articles', fontsize=10, fontweight='bold')
        ax4.set_title('Weekly Articles by Keyword (Last 12 Weeks) - Top 10 Keywords', fontsize=12, fontweight='bold', pad=15)
        ax4.legend(title='Keyword', bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=7)
        ax4.grid(axis='y', alpha=0.3)
        ax4.tick_params(axis='x', rotation=45, labelsize=8)
        
        # ============ MONTHLY BASIS ============
        # Monthly - Source wise count
        ax5 = fig.add_subplot(gs[2, 0])
        monthly_source = source_filtered_df.groupby(['month', 'source']).size().unstack(fill_value=0)
        
        monthly_source.plot(kind='bar', ax=ax5, width=0.8, stacked=True, alpha=0.8)
        ax5.set_xlabel('Month', fontsize=10, fontweight='bold')
        ax5.set_ylabel('Number of Articles', fontsize=10, fontweight='bold')
        ax5.set_title('Monthly Articles by Source - Top 10 Sources', fontsize=12, fontweight='bold', pad=15)
        ax5.legend(title='Source', bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=7)
        ax5.grid(axis='y', alpha=0.3)
        ax5.tick_params(axis='x', rotation=45, labelsize=8)
        
        # Monthly - Keyword wise count
        ax6 = fig.add_subplot(gs[2, 1])
        monthly_keyword = self.df.groupby(['month', 'keyword']).size().unstack(fill_value=0)
        
        # Show top 10 keywords
        monthly_keyword_top = monthly_keyword[[k for k in top_keywords if k in monthly_keyword.columns]]
        
        monthly_keyword_top.plot(kind='bar', ax=ax6, width=0.8, stacked=True, alpha=0.8)
        ax6.set_xlabel('Month', fontsize=10, fontweight='bold')
        ax6.set_ylabel('Number of Articles', fontsize=10, fontweight='bold')
        ax6.set_title('Monthly Articles by Keyword - Top 10 Keywords', fontsize=12, fontweight='bold', pad=15)
        ax6.legend(title='Keyword', bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=7)
        ax6.grid(axis='y', alpha=0.3)
        ax6.tick_params(axis='x', rotation=45, labelsize=8)
        
        plt.suptitle('Source-wise and Keyword-wise Article Distribution Analysis', 
                     fontsize=16, fontweight='bold', y=0.995)
        
        if save_path:
            plt.savefig(f"{save_path}_source_keyword_analysis.png", dpi=300, bbox_inches='tight')
        plt.show()
        
        print("\n=== Source-wise Daily Distribution (Last 30 days - Top 10 Sources) ===")
        print(daily_source_recent)
        print("\n=== Keyword-wise Daily Distribution (Last 30 days - Top 10 Keywords) ===")
        print(daily_keyword_top)
        print("\n=== Source-wise Monthly Distribution (Top 10 Sources) ===")
        print(monthly_source)
        print("\n=== Keyword-wise Monthly Distribution (Top 10 Keywords) ===")
        print(monthly_keyword_top)
    
    def generate_summary_report(self):
        """Generate a comprehensive summary report"""
        print("\n" + "="*80)
        print("NEWS ARTICLES DATA ANALYSIS - SUMMARY REPORT")
        print("="*80)
        
        print(f"\n📊 OVERALL STATISTICS")
        print(f"{'─'*80}")
        print(f"Total Articles: {len(self.df)}")
        print(f"Date Range: {self.df['effective_date'].min().date()} to {self.df['effective_date'].max().date()}")
        print(f"Total Sources: {self.df['source'].nunique()}")
        print(f"Total Keywords: {self.df['keyword'].nunique()}")
        print(f"Sent Articles: {len(self.df[self.df['is_sent']==True])}")
        print(f"Unsent Articles: {len(self.df[self.df['is_sent']==False])}")
        
        print(f"\n📈 ARTICLE TYPE BREAKDOWN")
        print(f"{'─'*80}")
        type_counts = self.df['article_type'].value_counts()
        for article_type, count in type_counts.items():
            percentage = (count / len(self.df)) * 100
            print(f"{article_type}: {count} ({percentage:.1f}%)")
        
        print(f"\n🔑 TOP 5 KEYWORDS")
        print(f"{'─'*80}")
        top_keywords = self.df['keyword'].value_counts().head(5)
        for i, (keyword, count) in enumerate(top_keywords.items(), 1):
            print(f"{i}. {keyword}: {count} articles")
        
        print(f"\n📰 TOP 5 SOURCES")
        print(f"{'─'*80}")
        top_sources = self.df['source'].value_counts().head(5)
        for i, (source, count) in enumerate(top_sources.items(), 1):
            print(f"{i}. {source}: {count} articles")
        
        print(f"\n📅 RECENT ACTIVITY")
        print(f"{'─'*80}")
        last_7_days = self.df[self.df['effective_date'] >= (datetime.now() - timedelta(days=7))]
        print(f"Articles in last 7 days: {len(last_7_days)}")
        print(f"Daily average (last 7 days): {len(last_7_days)/7:.1f}")
        
        last_30_days = self.df[self.df['effective_date'] >= (datetime.now() - timedelta(days=30))]
        print(f"Articles in last 30 days: {len(last_30_days)}")
        print(f"Daily average (last 30 days): {len(last_30_days)/30:.1f}")
        
        print(f"\n{'='*80}")
    
    def run_complete_analysis(self, save_plots=False, save_path="news_analysis"):
        """Run all analysis and generate all plots"""
        print("\n🚀 Starting Complete Data Analysis...\n")
        
        if not self.connect_and_fetch_data():
            print("Failed to load data. Exiting...")
            return
        
        # Generate summary report first
        self.generate_summary_report()
        
        print("\n📊 Generating visualizations...")
        
        # Generate all plots
        print("\n1️⃣  Generating: Articles by Source...")
        self.plot_articles_by_source(save_path if save_plots else None)
        
        print("\n2️⃣  Generating: Articles by Keyword...")
        self.plot_articles_by_keyword(save_path if save_plots else None)
        
        print("\n3️⃣  Generating: Monthly and Weekly Averages...")
        self.plot_monthly_weekly_averages(save_path if save_plots else None)
        
        print("\n4️⃣  Generating: API Keywords Analysis...")
        self.plot_api_keywords_analysis(save_path if save_plots else None)
        
        print("\n5️⃣  Generating: Scraping Keywords Analysis...")
        self.plot_scraping_keywords_analysis(save_path if save_plots else None)
        
        print("\n6️⃣  Generating: API vs Scraping Comparison...")
        self.plot_api_vs_scraping_comparison(save_path if save_plots else None)
        
        print("\n7️⃣  Generating: Source-wise and Keyword-wise Analysis...")
        self.plot_source_wise_keyword_analysis(save_path if save_plots else None)
        
        print("\n✅ Analysis Complete!")
        
        if save_plots:
            print(f"\n💾 All plots have been saved with prefix: {save_path}_*.png")
    
    def export_data_to_excel(self, filename="news_articles_analysis.xlsx"):
        """Export analyzed data to Excel with multiple sheets"""
        if self.df is None:
            print("No data loaded. Please run connect_and_fetch_data() first.")
            return
        
        print(f"\n📤 Exporting data to Excel: {filename}")
        
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            # Raw data
            self.df.to_excel(writer, sheet_name='Raw Data', index=False)
            
            # Summary statistics
            summary_data = {
                'Metric': [
                    'Total Articles',
                    'API Articles',
                    'Scraping Articles',
                    'Total Sources',
                    'Total Keywords',
                    'Sent Articles',
                    'Unsent Articles',
                    'Date Range Start',
                    'Date Range End'
                ],
                'Value': [
                    len(self.df),
                    len(self.df[self.df['article_type']=='API']),
                    len(self.df[self.df['article_type']=='Scraping']),
                    self.df['source'].nunique(),
                    self.df['keyword'].nunique(),
                    len(self.df[self.df['is_sent']==True]),
                    len(self.df[self.df['is_sent']==False]),
                    str(self.df['effective_date'].min().date()),
                    str(self.df['effective_date'].max().date())
                ]
            }
            pd.DataFrame(summary_data).to_excel(writer, sheet_name='Summary', index=False)
            
            # Articles by source
            source_counts = self.df['source'].value_counts().reset_index()
            source_counts.columns = ['Source', 'Count']
            source_counts.to_excel(writer, sheet_name='By Source', index=False)
            
            # Articles by keyword
            keyword_counts = self.df['keyword'].value_counts().reset_index()
            keyword_counts.columns = ['Keyword', 'Count']
            keyword_counts.to_excel(writer, sheet_name='By Keyword', index=False)
            
            # Monthly breakdown
            monthly_breakdown = self.df.groupby(['month', 'article_type']).size().unstack(fill_value=0)
            monthly_breakdown.to_excel(writer, sheet_name='Monthly Breakdown')
            
            # Weekly breakdown
            weekly_breakdown = self.df.groupby(['week', 'article_type']).size().unstack(fill_value=0)
            weekly_breakdown.tail(12).to_excel(writer, sheet_name='Weekly Breakdown (Recent)')
        
        print(f"✅ Data exported successfully to {filename}")


def main():
    """Main function to run the analysis"""
    
    # =================================================================
    # CONFIGURATION SECTION - Edit your database settings here
    # =================================================================
    
    MYSQL_CONFIG = {
        'host': 'host_name_or_ip',
        'database': 'database_name',
        'user': 'your_username',
        'password': 'your_password'
    }
    
    # =================================================================
    # END OF CONFIGURATION SECTION
    # =================================================================
    
    analyzer = NewsDataAnalyzer(MYSQL_CONFIG)
    
    print("=" * 80)
    print("NEWS ARTICLES DATA ANALYSIS TOOL")
    print("=" * 80)
    
    print("""
Choose an option:

1. Run Complete Analysis (All Charts + Summary)
2. Individual Chart - Articles by Source
3. Individual Chart - Articles by Keyword
4. Individual Chart - Monthly/Weekly Averages
5. Individual Chart - API Keywords Analysis
6. Individual Chart - Scraping Keywords Analysis
7. Individual Chart - API vs Scraping Comparison
8. Individual Chart - Source-wise & Keyword-wise Analysis (Daily/Weekly/Monthly)
9. Generate Summary Report Only
10. Export Data to Excel
11. Run Analysis and Save All Plots

Enter your choice (1-11): """)
    
    choice = input().strip()
    
    if choice == "1":
        analyzer.run_complete_analysis(save_plots=False)
    
    elif choice == "2":
        if analyzer.connect_and_fetch_data():
            analyzer.plot_articles_by_source()
    
    elif choice == "3":
        if analyzer.connect_and_fetch_data():
            analyzer.plot_articles_by_keyword()
    
    elif choice == "4":
        if analyzer.connect_and_fetch_data():
            analyzer.plot_monthly_weekly_averages()
    
    elif choice == "5":
        if analyzer.connect_and_fetch_data():
            analyzer.plot_api_keywords_analysis()
    
    elif choice == "6":
        if analyzer.connect_and_fetch_data():
            analyzer.plot_scraping_keywords_analysis()
    
    elif choice == "7":
        if analyzer.connect_and_fetch_data():
            analyzer.plot_api_vs_scraping_comparison()
    
    elif choice == "8":
        if analyzer.connect_and_fetch_data():
            analyzer.plot_source_wise_keyword_analysis()
    
    elif choice == "9":
        if analyzer.connect_and_fetch_data():
            analyzer.generate_summary_report()
    
    elif choice == "10":
        if analyzer.connect_and_fetch_data():
            filename = input("Enter filename for Excel export (default: news_articles_analysis.xlsx): ").strip()
            if not filename:
                filename = "news_articles_analysis.xlsx"
            if not filename.endswith('.xlsx'):
                filename += '.xlsx'
            analyzer.export_data_to_excel(filename)
    
    elif choice == "11":
        save_prefix = input("Enter prefix for saved files (default: news_analysis): ").strip()
        if not save_prefix:
            save_prefix = "news_analysis"
        analyzer.run_complete_analysis(save_plots=True, save_path=save_prefix)
    
    else:
        print("Invalid choice. Please run the program again and select 1-11.")


if __name__ == "__main__":
    main()