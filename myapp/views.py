from django.shortcuts import render
from django.http import JsonResponse
import pandas as pd
import matplotlib.pyplot as plt
import io
import urllib, base64
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
import matplotlib
from django.views.decorators.csrf import csrf_exempt

matplotlib.use('Agg') 

def home(request):
    return render(request, 'index.html')

def about(request):
    return render(request, 'about.html')

@csrf_exempt
def process_csv(request):
    if request.method == 'POST' and request.FILES.get('csv_file'):
        csv_file = request.FILES['csv_file']
        try:
            df = pd.read_csv(csv_file)

            required_cols = ['CustomerID', 'Gender', 'Age', 'Annual Income (k$)', 'Spending Score (1-100)']
            if not all(col in df.columns for col in required_cols):
                return JsonResponse({'status': 'error', 'error': 'Invalid CSV format. Missing required columns.'})

            X = df[['Annual Income (k$)', 'Spending Score (1-100)']].values

            kmeans = KMeans(n_clusters=5, init='k-means++', random_state=42)
            clusters = kmeans.fit_predict(X)
            df['Cluster'] = clusters

            sil_score = silhouette_score(X, clusters)
            quality_percentage = round(max(0, sil_score) * 100, 1)

            overview = {
                'total_customers': len(df),
                'avg_income': round(df['Annual Income (k$)'].mean(), 1),
                'avg_spending': round(df['Spending Score (1-100)'].mean(), 1),
                'model_accuracy': f"{quality_percentage}%"
            }

            cluster_names = {
                0: 'Careful Savers',
                1: 'Average Consumers',
                2: 'Target Customers',
                3: 'Impulse Spenders',
                4: 'Budget Conscious'
            }
            df['Segment'] = df['Cluster'].map(cluster_names)

            percentages = (df['Segment'].value_counts(normalize=True) * 100).round(1).to_dict()

            suggestions = {
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

            plt.figure(figsize=(8, 5))
            colors = ['red', 'blue', 'green', 'cyan', 'magenta']
            for i in range(5):
                plt.scatter(X[clusters == i, 0], X[clusters == i, 1], s=50, c=colors[i], label=cluster_names[i])
            plt.title('Customer Segments Strategy')
            plt.xlabel('Annual Income (k$)')
            plt.ylabel('Spending Score (1-100)')
            plt.legend()

            fig1 = plt.gcf()
            buf1 = io.BytesIO()
            fig1.savefig(buf1, format='png', bbox_inches='tight')
            buf1.seek(0)
            plot_cluster = base64.b64encode(buf1.read()).decode('utf-8')
            plt.close()

            plt.figure(figsize=(8, 5))
            df['Segment'].value_counts().plot(kind='bar', color='#2563eb')
            plt.title('Total Customers per Segment')
            plt.xlabel('Segment')
            plt.ylabel('Number of Customers')
            plt.xticks(rotation=45)

            fig2 = plt.gcf()
            buf2 = io.BytesIO()
            fig2.savefig(buf2, format='png', bbox_inches='tight')
            buf2.seek(0)
            plot_bar = base64.b64encode(buf2.read()).decode('utf-8')
            plt.close()

            table_html = df.drop(columns=['Cluster']).to_html(classes='dataframe', index=False)

            return JsonResponse({
                'status': 'success',
                'overview': overview,
                'percentages': percentages,
                'suggestions': suggestions,
                'plot_cluster': plot_cluster,
                'plot_bar': plot_bar,
                'table': table_html
            })
            
        except Exception as e:
            return JsonResponse({'status': 'error', 'error': str(e)})
            
    return JsonResponse({'status': 'error', 'error': 'Invalid request'})