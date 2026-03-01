import pandas as pd
import io
import base64
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

def home_view(request):
    return render(request, 'index.html')

def about_view(request):
    return render(request, 'about.html')

def assign_business_value(row):
    income = row['Annual Income (k$)']
    spend = row['Spending Score (1-100)']
    
    if income > 70 and spend > 70:
        return 'High Value - Target Customers'
    elif income > 70 and spend <= 40:
        return 'Medium Value - Careful Savers'
    elif income <= 40 and spend > 70:
        return 'Medium Value - Careless Spenders'
    elif income <= 40 and spend <= 40:
        return 'Low Value - Sensible Customers'
    else:
        return 'Average Value - General Public'

@csrf_exempt
def process_csv(request):
    if request.method == 'POST' and request.FILES.get('csv_file'):
        file = request.FILES['csv_file']
        
        try:
            df = pd.read_csv(file)
            
            if 'Annual Income (k$)' not in df.columns or 'Spending Score (1-100)' not in df.columns:
                return JsonResponse({'error': 'Please upload the correct Mall Customers CSV.'}, status=400)

            X = df[['Annual Income (k$)', 'Spending Score (1-100)']].values
            kmeans = KMeans(n_clusters=5, init='k-means++', random_state=42)
            df['Cluster'] = kmeans.fit_predict(X)
            df['Customer_Value_Category'] = df.apply(assign_business_value, axis=1)

            total_customers = len(df)
            avg_income = round(df['Annual Income (k$)'].mean(), 2)
            avg_spending = round(df['Spending Score (1-100)'].mean(), 2)
            
            segment_counts = df['Customer_Value_Category'].value_counts()
            segment_percentages = {cat: round((count / total_customers) * 100, 1) for cat, count in segment_counts.items()}

            manager_suggestions = {
                'High Value - Target Customers': [
                    "Offer exclusive VIP memberships with premium perks.",
                    "Send personalized invitations to private sales or early-access events.",
                    "Introduce high-end, luxury brands to match their income.",
                    "Assign dedicated personal shoppers to enhance their experience.",
                    "Do not rely on heavy discounts; focus on premium quality and exclusivity."
                ],
                'Medium Value - Careful Savers': [
                    "Promote high-quality, durable, and value-for-money products.",
                    "Offer loyalty programs that reward long-term engagement.",
                    "Provide strong warranties and guarantees to build trust.",
                    "Run targeted 'buy-one-get-one' or volume discount campaigns.",
                    "Highlight functional benefits rather than luxury appeal."
                ],
                'Medium Value - Careless Spenders': [
                    "Push trendy, fast-fashion, and impulse-buy items.",
                    "Use limited-time offers and flash sales to trigger urgency.",
                    "Engage them heavily through social media and influencer marketing.",
                    "Offer flexible payment options like 'Buy Now, Pay Later'.",
                    "Place attractive, low-barrier items near checkout counters."
                ],
                'Low Value - Sensible Customers': [
                    "Focus on essential goods and everyday necessities.",
                    "Offer deep discounts, clearance sales, and budget-friendly bundles.",
                    "Market free family-friendly events at the mall to increase footfall.",
                    "Ensure food court and entertainment options remain affordable.",
                    "Use point-based loyalty systems that offer tangible cashback."
                ],
                'Average Value - General Public': [
                    "Run standard seasonal promotions and holiday sales.",
                    "Maintain a diverse mix of mid-tier retail brands.",
                    "Enhance the overall mall experience (e.g., better seating, free Wi-Fi).",
                    "Promote family-oriented entertainment like cinemas and arcades.",
                    "Collect feedback regularly to understand shifting preferences."
                ]
            }

            plt.figure(figsize=(10, 6))
            categories = df['Customer_Value_Category'].unique()
            colors = ['#ef4444', '#3b82f6', '#10b981', '#f59e0b', '#8b5cf6']
            color_map = dict(zip(categories, colors))

            for cat in categories:
                subset = df[df['Customer_Value_Category'] == cat]
                plt.scatter(subset['Annual Income (k$)'], subset['Spending Score (1-100)'], 
                            s=100, label=cat, alpha=0.7, c=color_map[cat])
            
            plt.scatter(kmeans.cluster_centers_[:, 0], kmeans.cluster_centers_[:, 1], 
                        s=250, c='yellow', marker='*', edgecolor='black', label='Algorithm Centroids')
            
            plt.title('Customer Segments Analysis', fontsize=14, pad=15)
            plt.xlabel('Annual Income (k$)')
            plt.ylabel('Spending Score (1-100)')
            plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
            plt.tight_layout()

            buffer1 = io.BytesIO()
            plt.savefig(buffer1, format='png', transparent=True, bbox_inches='tight')
            buffer1.seek(0)
            plot_cluster = base64.b64encode(buffer1.getvalue()).decode('utf-8')
            plt.close()

            plt.figure(figsize=(10, 5))
            value_counts = df['Customer_Value_Category'].value_counts()
            bar_colors = [color_map[cat] for cat in value_counts.index]
            bars = plt.bar(value_counts.index, value_counts.values, color=bar_colors)
            plt.title('Total Customers per Category', fontsize=14, pad=15)
            plt.ylabel('Number of Customers')
            plt.xticks(rotation=25, ha='right')
            for bar in bars:
                yval = bar.get_height()
                plt.text(bar.get_x() + bar.get_width()/2, yval + 0.5, int(yval), ha='center', va='bottom', fontweight='bold')
            plt.tight_layout()

            buffer2 = io.BytesIO()
            plt.savefig(buffer2, format='png', transparent=True, bbox_inches='tight')
            buffer2.seek(0)
            plot_bar = base64.b64encode(buffer2.getvalue()).decode('utf-8')
            plt.close()

            df_manager_view = df.drop('Cluster', axis=1)
            table_html = df_manager_view.to_html(classes='data-table', index=False)

            return JsonResponse({
                'status': 'success',
                'overview': {
                    'total_customers': total_customers,
                    'avg_income': avg_income,
                    'avg_spending': avg_spending
                },
                'percentages': segment_percentages,
                'suggestions': manager_suggestions,
                'plot_cluster': plot_cluster,
                'plot_bar': plot_bar,
                'table': table_html
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
            
    return JsonResponse({'error': 'No file uploaded'}, status=400)