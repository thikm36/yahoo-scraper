import streamlit as st
import requests
from bs4 import BeautifulSoup
import time
import os
import csv
import pandas as pd
import shutil
from urllib.parse import urlparse

st.set_page_config(page_title="ヤフオクツール", page_icon="🏺")
st.title("ヤフオクスクレイパー（完全版）")

keyword = st.text_input("検索キーワード", "ハイゼットトラック S500 マッドガード")
max_pages = st.number_input("取得ページ数（1ページ100件）", min_value=1, max_value=5, value=1)
run_button = st.button("スクレイピング開始！")

if run_button:
    img_folder = "product_images"
    if os.path.exists(img_folder):
        shutil.rmtree(img_folder)
    os.makedirs(img_folder)
    
    results = []
    total_count = 0  # 連番用のカウント
    progress_bar = st.progress(0)
    
    for page in range(1, max_pages + 1):
        st.write(f"【{page}ページ目】解析中...")
        start_item = (page - 1) * 100 + 1
        url = f"https://auctions.yahoo.co.jp/search/search?p={keyword}&s1=cbids&o1=a&n=100&b={start_item}"
        
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        items = soup.select('.Product') 
        
        if not items:
            st.warning("これ以上商品がないぜ！")
            break
            
        for item in items:
            title_tag = item.select_one('.Product__titleLink')
            price_tag = item.select_one('.Product__priceValue')
            postage_tag = item.select_one('.Product__postage')
            img_tag = item.select_one('.Product__imageData')
            link_tag = item.select_one('a')
            bonus_tag = item.select_one('.Product__bonus')
            
            if title_tag and price_tag and link_tag:
                # 価格の抽出
                price_str = price_tag.text.strip().replace('円', '').replace(',', '').replace('即決', '').strip()
                price_int = int(price_str) if price_str.isdigit() else 0
                
                # 送料の抽出
                postage_text = postage_tag.text.strip() if postage_tag else ""
                shipping_str = "0" if "送料無料" in postage_text else postage_text.replace('＋送料', '').replace('円', '').replace(',', '').strip()
                shipping_int = int(shipping_str) if shipping_str.isdigit() else 0
                
                # 出品者IDの抽出
                seller_id = bonus_tag.get('data-auction-auc-seller-id', '不明') if bonus_tag else '不明'
                
                total_count += 1
                
                # 画像のダウンロード（連番付き）
                if img_tag and img_tag.has_attr('src'):
                    try:
                        auction_id = link_tag['data-auction-id']
                        img_url = img_tag['src']
                        clean_filename = os.path.basename(urlparse(img_url).path)
                        # 連番 + ID + ファイル名
                        save_name = f"{total_count:03d}_{auction_id}_{clean_filename}"
                        file_path = os.path.join(img_folder, save_name)
                        with open(file_path, 'wb') as f:
                            f.write(requests.get(img_url).content)
                    except:
                        pass
                
                # 結果を保存
                results.append({
                    "商品名": title_tag.text.strip(),
                    "価格": price_int,
                    "送料": shipping_int,
                    "合計": price_int + shipping_int,
                    "出品者ID": seller_id,
                    "URL": title_tag['href']
                })
        
        progress_bar.progress(page / max_pages)
        time.sleep(2)

    if results:
        df = pd.DataFrame(results)
        st.dataframe(df)
        
        csv = df.to_csv(index=False).encode('utf-8-sig')
        st.download_button("CSVをダウンロード", csv, "results.csv", "text/csv")
        
        shutil.make_archive("product_images", 'zip', "product_images")
        with open("product_images.zip", "rb") as fp:
            st.download_button("画像ZIPをダウンロード", fp, "images.zip", "application/zip")
        st.success(f"全 {total_count} 件の取得完了だぜ！")
    else:
        st.error("データが取れなかったぜ…")