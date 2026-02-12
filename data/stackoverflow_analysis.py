import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from wordcloud import WordCloud
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from collections import Counter, defaultdict
import re
from datetime import datetime
import numpy as np

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei']  # 用来正常显示中文标签
plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号

# 读取数据
def load_data(file_path):
    data = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                data.append(json.loads(line.strip()))
            except json.JSONDecodeError:
                pass
    return pd.DataFrame(data)

# 数据清洗
def clean_data(df):
    # 移除空值
    df = df.dropna(subset=['question_body', 'answer_body'])
    
    # 移除分数过低的问答
    df = df[(df['question_score'] >= 5) | (df['answer_score'] >= 5)]
    
    # 转换时间格式
    df['question_creation_date'] = pd.to_datetime(df['question_creation_date'])
    df['answer_creation_date'] = pd.to_datetime(df['answer_creation_date'])
    
    return df

# 统计最常见的标签
def analyze_tag_distribution(df, top_n=20):
    # 展平标签列表
    all_tags = [tag for tags in df['tags'] for tag in tags]
    tag_counts = Counter(all_tags)
    
    # 获取前N个最常见的标签
    top_tags = tag_counts.most_common(top_n)
    tags, counts = zip(*top_tags)
    
    return tags, counts

# 分析评分分布
def analyze_score_distribution(df):
    return df[['question_score', 'answer_score', 'view_count']]

# 分析时间趋势
def analyze_time_trends(df):
    # 按月份分组
    df['year_month'] = df['question_creation_date'].dt.to_period('M')
    monthly_counts = df.groupby('year_month').size().reset_index(name='count')
    monthly_counts['year_month'] = monthly_counts['year_month'].astype(str)
    
    return monthly_counts

# 主题聚类
def cluster_topics(df, n_clusters=5):
    # 提取问题标题和内容
    texts = df['title'] + ' ' + df['question_body']
    
    # 文本预处理
    texts = texts.apply(lambda x: re.sub(r'[^\w\s]', '', x.lower()))
    
    # TF-IDF向量化
    vectorizer = TfidfVectorizer(stop_words='english', max_features=1000)
    X = vectorizer.fit_transform(texts)
    
    # K-means聚类
    kmeans = KMeans(n_clusters=n_clusters, random_state=42)
    df['cluster'] = kmeans.fit_predict(X)
    
    # 获取每个聚类的关键词
    feature_names = vectorizer.get_feature_names_out()
    centroids = kmeans.cluster_centers_
    cluster_keywords = []
    
    for i in range(n_clusters):
        top_indices = centroids[i].argsort()[-10:][::-1]
        top_words = [feature_names[idx] for idx in top_indices]
        cluster_keywords.append(top_words)
    
    return df, cluster_keywords

# 分析标签关联
def analyze_tag_relationships(df, top_n=15):
    # 获取前N个最常见的标签
    all_tags = [tag for tags in df['tags'] for tag in tags]
    top_tags = [tag for tag, _ in Counter(all_tags).most_common(top_n)]
    
    # 构建标签共现矩阵
    tag_matrix = np.zeros((len(top_tags), len(top_tags)))
    tag_index = {tag: i for i, tag in enumerate(top_tags)}
    
    for tags in df['tags']:
        # 只考虑前N个标签
        common_tags = [tag for tag in tags if tag in top_tags]
        
        # 计算共现
        for i, tag1 in enumerate(common_tags):
            for tag2 in common_tags[i+1:]:
                tag_matrix[tag_index[tag1]][tag_index[tag2]] += 1
                tag_matrix[tag_index[tag2]][tag_index[tag1]] += 1
    
    return top_tags, tag_matrix

# 生成标签云
def generate_tag_cloud(tags, counts, output_path='tag_cloud.png'):
    # 创建标签频率字典
    tag_freq = dict(zip(tags, counts))
    
    # 生成标签云
    wordcloud = WordCloud(width=800, height=400, background_color='white', 
                         font_path='C:\\Windows\\Fonts\\simhei.ttf')
    wordcloud.generate_from_frequencies(tag_freq)
    
    # 保存并显示
    plt.figure(figsize=(10, 5))
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis('off')
    plt.title('Python 相关标签云')
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.show()

# 生成评分分布图
def plot_score_distribution(scores, output_path='score_distribution.png'):
    fig, axes = plt.subplots(3, 1, figsize=(12, 15))
    
    # 问题评分分布
    sns.histplot(scores['question_score'], bins=50, ax=axes[0])
    axes[0].set_title('问题评分分布')
    axes[0].set_xlabel('评分')
    axes[0].set_ylabel('数量')
    
    # 回答评分分布
    sns.histplot(scores['answer_score'], bins=50, ax=axes[1])
    axes[1].set_title('回答评分分布')
    axes[1].set_xlabel('评分')
    axes[1].set_ylabel('数量')
    
    # 浏览量分布（对数刻度）
    sns.histplot(np.log1p(scores['view_count']), bins=50, ax=axes[2])
    axes[2].set_title('浏览量分布（对数刻度）')
    axes[2].set_xlabel('浏览量（log1p）')
    axes[2].set_ylabel('数量')
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.show()

# 生成时间序列图
def plot_time_trends(monthly_counts, output_path='time_trends.png'):
    plt.figure(figsize=(14, 6))
    plt.plot(monthly_counts['year_month'], monthly_counts['count'], marker='o')
    plt.title('Python 相关问题的时间趋势')
    plt.xlabel('时间')
    plt.ylabel('问题数量')
    plt.xticks(rotation=45)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.show()

# 生成标签关联热力图
def plot_tag_heatmap(tags, matrix, output_path='tag_heatmap.png'):
    plt.figure(figsize=(12, 10))
    sns.heatmap(matrix, annot=False, xticklabels=tags, yticklabels=tags, cmap='YlOrRd')
    plt.title('标签关联热力图')
    plt.xticks(rotation=45, ha='right')
    plt.yticks(rotation=0)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.show()

# 主函数
def main():
    # 数据文件路径
    data_file = 'stackoverflow-python-qa-cleaned.jsonl'
    
    # 加载和清洗数据
    print("加载数据中...")
    df = load_data(data_file)
    df = clean_data(df)
    print(f"清洗后的数据量: {len(df)}")
    
    # 分析标签分布
    print("分析标签分布...")
    tags, counts = analyze_tag_distribution(df)
    print("最常见的标签:", list(tags[:10]))
    
    # 生成标签云
    generate_tag_cloud(tags, counts)
    
    # 分析评分分布
    print("分析评分分布...")
    scores = analyze_score_distribution(df)
    plot_score_distribution(scores)
    
    # 分析时间趋势
    print("分析时间趋势...")
    monthly_counts = analyze_time_trends(df)
    plot_time_trends(monthly_counts)
    
    # 分析标签关联
    print("分析标签关联...")
    top_tags, tag_matrix = analyze_tag_relationships(df)
    plot_tag_heatmap(top_tags, tag_matrix)
    
    # 主题聚类
    print("进行主题聚类...")
    df_clustered, cluster_keywords = cluster_topics(df)
    print("各聚类的关键词:")
    for i, keywords in enumerate(cluster_keywords):
        print(f"聚类 {i+1}: {', '.join(keywords[:5])}")
    
    # 保存分析结果
    df.to_csv('stackoverflow_analysis_results.csv', index=False, encoding='utf-8-sig')
    print("分析结果已保存到 stackoverflow_analysis_results.csv")

if __name__ == "__main__":
    main()
