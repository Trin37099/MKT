import pandas as pd
import streamlit as st
import numpy as np
from datetime import datetime
import datetime
import altair as alt
from openpyxl import load_workbook
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objs as go
import plotly.colors as pc
import re
import warnings
import calendar
warnings.filterwarnings('ignore')
import pycountry


st.set_page_config(
    page_title="HWS",
    layout = 'wide',
)
st.title('Hotel Website')

st.subheader('Please Upload Excel Files')
uploaded_files = st.file_uploader("Choose a Excel file",type = 'xlsx', accept_multiple_files=True)
if uploaded_files:
    all= []
    for uploaded_file in uploaded_files:
        try:
            for uploaded_file in uploaded_files:
                df = pd.read_excel(uploaded_file, thousands=',', skiprows=[0,1,2,3,4,5,6])
                all.append(df)
        except Exception as e:
            st.write(f"Error reading file: {uploaded_file.name}")
            st.write(e)
    if all:
            all = pd.concat(all)

            def clean(all):
                all = all.drop(['No.','Stay Month','Day of week','Child Code','Campaign'
                                ,'By Partner','Note','utm_id','utm_term','Guest Name','Email','Room Revenue'], axis=1)
                all[['Gender','Phone']] = all[['Gender','Phone']].fillna('Unknown')
                all[['Payment Gateway','Payment Scheme']] = all[['Payment Gateway','Payment Scheme']].fillna('None')
                all['Access Code'] = all['Access Code'].fillna('Not used')
                all[['Booking Number','Phone']] = all[['Booking Number','Phone']].astype('str')
                all = all.rename(columns={'Campaign.1': 'Campaign','# of night':'LOS','# of room':'Quantity','# of room night':'RN'})
                #all = all.fillna('None')
                return all

            def convert_to_iso3(country_name):
                try:
                    return pycountry.countries.get(name=country_name).alpha_3
                except:
                    return None
                
            all = clean(all)
            def perform(all): 
                all1 = all.copy()
                all1["Check-in"] = pd.to_datetime(all1["Check-in"], format='%d-%m-%Y')
                all1['Booking Date'] = pd.to_datetime(all1['Booking Date'], format='%d-%m-%Y')
                all1["Check-out"] = pd.to_datetime(all1["Check-out"], format='%d-%m-%Y')
                value_ranges = [-1, 0, 1, 2, 3, 4, 5, 6, 7,8, 14, 30, 90, 120]
                labels = ['-one', 'zero', 'one', 'two', 'three', 'four', 'five', 'six','seven', '8-14', '14-30', '31-90', '90-120', '120+']
                LT11 = [-1, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30,31,90, 120, float('inf')]
                LT22 = ['.-1.', '.0.', '.1.', '.2.', '.3.', '.4.', '.5.', '.6.', '.7.', '.8.', '.9.', '.10.', '.11.', '.12.', '.13.', '.14.', '.15.', '.16.', '.17.', '.18.', '.19.', '.20.', '.21.', '.22.', '23.', '.24.', '25.', '.26.', '.27.', '.28.', '.29.', '.30.', '31-90.', '91-120', '120.+']
                all1['Lead time range1'] = pd.cut(all1['Lead Time'], bins=LT11, labels=LT22, right=False)
                all1['Lead time range'] = pd.cut(all1['Lead Time'], bins=value_ranges + [float('inf')], labels=labels, right=False)
                all1['Room'] = all1['Room type'].str.upper()
                all1['ADR'] = (all1['Total Revenue']/all1['LOS'])/all1['Quantity']
                all1['iso_alpha'] =  all1['Booking Location'].apply(convert_to_iso3)
                all1['iso_alpha1'] =  all1['Nationality'].apply(convert_to_iso3)
                return all1

            all2 =  perform(all)

            channels = all2['Booking Source'].unique()
            room_type_options = all2['Room type'].unique().tolist()
            bs_options = all2['Booking Status'].unique().tolist()

            selected_channels = st.sidebar.multiselect('Select channels. ', channels, default=[], key='channels_select')
            selected_room_types = st.sidebar.multiselect('Select room types.', room_type_options, default=[], key='room_types_select')
            selected_room_bs = st.sidebar.multiselect('Select Booking status', bs_options, default=[], key='bs_select')

            tab1, tab_stay = st.tabs(['Book on date','Stay on date'])
            with tab1:
                if selected_channels:
                    filtered_df = all2[all2['Booking Source'].isin(selected_channels)]
                    if selected_room_types:
                        if 'All' not in selected_room_types:
                            filtered_df = filtered_df[filtered_df['Room type'].isin(selected_room_types)]
                    else:
                        if selected_room_types:
                            if 'All' not in selected_room_types:
                                filtered_df = all2[all2['Room type'].isin(selected_room_types)]
                else:
                    filtered_df = all2
                if selected_room_bs:
                    if 'All' not in selected_room_bs:
                        filtered_df = filtered_df[filtered_df['Booking Status'].isin(selected_room_bs)]

                month_dict = {v: k for k,v in enumerate(calendar.month_name)}
                months = list(calendar.month_name)[1:]
                selected_month = st.multiselect('Select a month', months)
                selected_year = st.selectbox('Select a year ', ['2022', '2023', '2024','2025','2026'], index=1)

                if selected_month and selected_year:
                                selected_month_nums = [month_dict[month_name] for month_name in selected_month]
                                filtered_df = filtered_df[
                                    (filtered_df['Booking Date'].dt.month.isin(selected_month_nums)) &
                                    (filtered_df['Booking Date'].dt.year == int(selected_year))
                                ]
                elif selected_month:
                                selected_month_nums = [month_dict[month_name] for month_name in selected_month]
                                filtered_df = filtered_df[filtered_df['Booking Date'].dt.month.isin(selected_month_nums)]
                elif selected_year:
                                filtered_df = filtered_df[filtered_df['Booking Date'].dt.year == int(selected_year)]

                
                col1 , col2 ,col3 = st.columns(3)
                with col2:
                    filter_LT = st.checkbox('Filter by LT ')
                    if filter_LT:
                        min_val, max_val = int(filtered_df['Lead Time'].min()), int(filtered_df['Lead Time'].max())
                        LT_min, LT_max = st.slider('Select a range of LT', min_val, max_val, (min_val, max_val))
                        filtered_df = filtered_df[(filtered_df['Lead Time'] >= LT_min) & (filtered_df['Lead Time'] <= LT_max)]
                    else:
                        filtered_df = filtered_df.copy()
                with col1:
                    filter_LOS = st.checkbox('Filter by LOS ')
                    if filter_LOS:
                        min_val, max_val = int(filtered_df['LOS'].min()), int(filtered_df['LOS'].max())
                        LOS_min, LOS_max = st.slider('Select a range of LOS', min_val, max_val, (min_val, max_val))
                        filtered_df = filtered_df[(filtered_df['LOS'] >= LOS_min) & (filtered_df['LOS'] <= LOS_max)]
                    else:   
                        filtered_df = filtered_df.copy()
                with col3:
                    filter_rn = st.checkbox('Filter by Roomnight')
                    if filter_rn:
                        min_val, max_val = int(filtered_df['RN'].min()), int(filtered_df['RN'].max())
                        rn_min, rn_max = st.slider('Select a range of roomnights', min_val, max_val, (min_val, max_val))
                        filtered_df = filtered_df[(filtered_df['RN'] >= rn_min) & (filtered_df['RN'] <= rn_max)]
                    else:
                        filtered_df = filtered_df.copy()

                table = filtered_df.copy()
                table['Stay'] = table.apply(lambda row: pd.date_range(row['Check-in'], row['Check-out']- pd.Timedelta(days=1)), axis=1)
                table = table.explode('Stay').reset_index(drop=True)
                bb,ss = st.tabs(['**ADR by Room type and channel (Booked)**','**ADR by Room type and channel (Stay)**'])
                with ss :
                    ADR_S,LT_S,LOS_S = st.tabs(['**ADR by channel and room type**','**LT by channel and room type**','**LOS by channel and room type**'])
                    with ADR_S:
                        st.markdown('**avg ADR without comm and ABF by channel and room type (if you do not filter month, it would be all month)**')
                        df_january = table[['Stay','Booking Source','Room type','ADR']]
                        avg_adr = df_january.groupby(['Booking Source', 'Room type'])['ADR'].mean()
                        result = avg_adr.reset_index().pivot_table(values='ADR', index='Booking Source', columns='Room type', fill_value=np.nan)
                        result.loc['Grand Total'] = result.mean()
                        result.at['Grand Total', 'Booking Source'] = 'Grand Total'
                        avg_adr_all_room_type = df_january.groupby(['Booking Source'])['ADR'].mean()
                        result['ALL ROOM TYPE'] = avg_adr_all_room_type
                        result = result.drop(columns='Booking Source')
                        result = result.applymap(lambda x: int(x) if not pd.isna(x) else np.nan)
                        st.write(result, use_container_width=True)
                    with LOS_S:
                        st.markdown('**avg LOS without comm and ABF by Booking Source and room type (if you do not filter month, it would be all month)**')
                        df_january = table[['Stay','Booking Source','Room type','LOS']]
                        avg_adr = df_january.groupby(['Booking Source', 'Room type'])['LOS'].mean()
                        result = avg_adr.reset_index().pivot_table(values='LOS', index='Booking Source', columns='Room type', fill_value=np.nan)
                        result.loc['Grand Total'] = result.mean()
                        result.at['Grand Total', 'Booking Source'] = 'Grand Total'
                        avg_adr_all_room_type = df_january.groupby(['Booking Source'])['LOS'].mean()
                        result['ALL ROOM TYPE'] = avg_adr_all_room_type
                        result = result.drop(columns='Booking Source')
                        result = result.applymap(lambda x: int(x) if not pd.isna(x) else np.nan)
                        st.write(result, use_container_width=True)
                    with LT_S:
                        st.markdown('**avg LT without comm and ABF by Booking Source and room type (if you do not filter month, it would be all month)**')
                        df_january = table[['Stay','Booking Source','Room type','Lead Time']]
                        avg_adr = df_january.groupby(['Booking Source', 'Room type'])['Lead Time'].mean()
                        result = avg_adr.reset_index().pivot_table(values='Lead Time', index='Booking Source', columns='Room type', fill_value=np.nan)
                        result.loc['Grand Total'] = result.mean()
                        result.at['Grand Total', 'Booking Source'] = 'Grand Total'
                        avg_adr_all_room_type = df_january.groupby(['Booking Source'])['Lead Time'].mean()
                        result['ALL ROOM TYPE'] = avg_adr_all_room_type
                        result = result.drop(columns='Booking Source')
                        result = result.applymap(lambda x: int(x) if not pd.isna(x) else np.nan)
                        st.write(result, use_container_width=True)
                with bb :
                    ADR_S,LT_S,LOS_S = st.tabs(['**ADR by Booking Source and room type**','**LT by Booking Source and room type**','**LOS by Booking Source and room type**'])
                    with ADR_S:
                        st.markdown('**avg ADR without comm and ABF by Booking Source and room type (if you do not filter month, it would be all month)**')
                        df_january = filtered_df[['Booking Date','Booking Source','Room type','ADR']]
                        avg_adr = df_january.groupby(['Booking Source', 'Room type'])['ADR'].mean()
                        result = avg_adr.reset_index().pivot_table(values='ADR', index='Booking Source', columns='Room type', fill_value=np.nan)
                        result.loc['Grand Total'] = result.mean()
                        result.at['Grand Total', 'Booking Source'] = 'Grand Total'
                        avg_adr_all_room_type = df_january.groupby(['Booking Source'])['ADR'].mean()
                        result['ALL ROOM TYPE'] = avg_adr_all_room_type
                        result = result.drop(columns='Booking Source')
                        result = result.applymap(lambda x: int(x) if not pd.isna(x) else np.nan)
                        st.write(result, use_container_width=True)
                    with LOS_S:
                        st.markdown('**avg LOS without comm and ABF by Booking Source and room type (if you do not filter month, it would be all month)**')
                        df_january = filtered_df[['Booking Date','Booking Source','Room type','LOS']]
                        avg_adr = df_january.groupby(['Booking Source', 'Room type'])['LOS'].mean()
                        result = avg_adr.reset_index().pivot_table(values='LOS', index='Booking Source', columns='Room type', fill_value=np.nan)
                        result.loc['Grand Total'] = result.mean()
                        result.at['Grand Total', 'Booking Source'] = 'Grand Total'
                        avg_adr_all_room_type = df_january.groupby(['Booking Source'])['LOS'].mean()
                        result['ALL ROOM TYPE'] = avg_adr_all_room_type
                        result = result.drop(columns='Booking Source')
                        result = result.applymap(lambda x: int(x) if not pd.isna(x) else np.nan)
                        st.write(result, use_container_width=True)
                    with LT_S:
                        st.markdown('**avg LT without comm and ABF by Booking Source and room type (if you do not filter month, it would be all month)**')
                        df_january = filtered_df[['Booking Date','Booking Source','Room type','Lead Time']]
                        avg_adr = df_january.groupby(['Booking Source', 'Room type'])['Lead Time'].mean()
                        result = avg_adr.reset_index().pivot_table(values='Lead Time', index='Booking Source', columns='Room type', fill_value=np.nan)
                        result.loc['Grand Total'] = result.mean()
                        result.at['Grand Total', 'Booking Source'] = 'Grand Total'
                        avg_adr_all_room_type = df_january.groupby(['Booking Source'])['Lead Time'].mean()
                        result['ALL ROOM TYPE'] = avg_adr_all_room_type
                        result = result.drop(columns='Booking Source')
                        result = result.applymap(lambda x: int(x) if not pd.isna(x) else np.nan)
                        st.write(result, use_container_width=True)

                channels = filtered_df['Booking Source'].unique()
                num_colors = len(channels)
                colors = px.colors.qualitative.Plotly
                color_scale =  {channel: colors[i % num_colors] for i, channel in enumerate(channels)}
                ch,rn,med,rt = st.tabs(['Count booking by Source','Count booking by Rate name','Count booking by utm medium','Count booking by Room type'])
                with ch:
                    grouped = filtered_df.groupby(['Booking Date', 'Booking Source']).size().reset_index(name='counts')
                    fig = px.bar(grouped, x='Booking Date', y='counts', color='Booking Source',color_discrete_map=color_scale, barmode='stack')
                    st.plotly_chart(fig,use_container_width=True)
                with rn :
                    grouped = filtered_df.groupby(['Booking Date', 'Rate Name']).size().reset_index(name='counts')
                    fig = px.bar(grouped, x='Booking Date', y='counts', color='Rate Name',color_discrete_map=color_scale, barmode='stack')
                    st.plotly_chart(fig,use_container_width=True)
                with med :
                    grouped = filtered_df.groupby(['Booking Date', 'utm_medium']).size().reset_index(name='counts')
                    fig = px.bar(grouped, x='Booking Date', y='counts', color='utm_medium',color_discrete_map=color_scale, barmode='stack')
                    st.plotly_chart(fig,use_container_width=True)     
                with rt :
                    grouped = filtered_df.groupby(['Booking Date', 'Room type']).size().reset_index(name='counts')
                    fig = px.bar(grouped, x='Booking Date', y='counts', color='Room type',color_discrete_map=color_scale, barmode='stack')
                    st.plotly_chart(fig,use_container_width=True)                 
                col1, col2 = st.columns(2)
                with col1:
                    ch,rn,med,rt = st.tabs(['Count LOS by Source','Count LOS by Rate name','Count LOS by utm medium','Count LOS by Room type'])
                    with ch:
                        grouped = filtered_df.groupby(['LOS', 'Booking Source']).size().reset_index(name='counts')
                        fig = px.bar(grouped, x='LOS', y='counts', color='Booking Source',color_discrete_map=color_scale, barmode='stack')
                        st.plotly_chart(fig,use_container_width=True)
                    with rn :
                        grouped = filtered_df.groupby(['LOS', 'Rate Name']).size().reset_index(name='counts')
                        fig = px.bar(grouped, x='LOS', y='counts', color='Rate Name',color_discrete_map=color_scale, barmode='stack')
                        st.plotly_chart(fig,use_container_width=True)
                    with med :
                        grouped = filtered_df.groupby(['LOS', 'utm_medium']).size().reset_index(name='counts')
                        fig = px.bar(grouped, x='LOS', y='counts', color='utm_medium',color_discrete_map=color_scale, barmode='stack')
                        st.plotly_chart(fig,use_container_width=True)     
                    with rt :
                        grouped = filtered_df.groupby(['LOS', 'Room type']).size().reset_index(name='counts')
                        fig = px.bar(grouped, x='LOS', y='counts', color='Room type',color_discrete_map=color_scale, barmode='stack')
                        st.plotly_chart(fig,use_container_width=True)      
                with col2:
                    l1,l2,l3 = st.tabs(['Lead time (0-7)','Lead time (0-30)','Lead time non grouping'])
                    with l1:
                        ch,rn,med,rt = st.tabs(['Count LT by Source','Count booking by Rate name','Count LT by utm medium','Count LT by Room type'])
                        with ch:
                            grouped = filtered_df.groupby(['Lead time range', 'Booking Source']).size().reset_index(name='counts')
                            fig = px.bar(grouped, x='Lead time range', y='counts', color='Booking Source',color_discrete_map=color_scale, barmode='stack')
                            st.plotly_chart(fig,use_container_width=True)
                        with rn :
                            grouped = filtered_df.groupby(['Lead time range', 'Rate Name']).size().reset_index(name='counts')
                            fig = px.bar(grouped, x='Lead time range', y='counts', color='Rate Name',color_discrete_map=color_scale, barmode='stack')
                            st.plotly_chart(fig,use_container_width=True)
                        with med :
                            grouped = filtered_df.groupby(['Lead time range', 'utm_medium']).size().reset_index(name='counts')
                            fig = px.bar(grouped, x='Lead time range', y='counts', color='utm_medium',color_discrete_map=color_scale, barmode='stack')
                            st.plotly_chart(fig,use_container_width=True)     
                        with rt :
                            grouped = filtered_df.groupby(['Lead time range', 'Room type']).size().reset_index(name='counts')
                            fig = px.bar(grouped, x='Lead time range', y='counts', color='Room type',color_discrete_map=color_scale, barmode='stack')
                            st.plotly_chart(fig,use_container_width=True)
                    with l2:
                        ch,rn,med,rt = st.tabs(['Count LT by Source','Count booking by Rate name','Count LT by utm medium','Count LT by Room type'])
                        with ch:
                            grouped = filtered_df.groupby(['Lead time range1', 'Booking Source']).size().reset_index(name='counts')
                            fig = px.bar(grouped, x='Lead time range1', y='counts', color='Booking Source',color_discrete_map=color_scale, barmode='stack')
                            st.plotly_chart(fig,use_container_width=True)
                        with rn :
                            grouped = filtered_df.groupby(['Lead time range1', 'Rate Name']).size().reset_index(name='counts')
                            fig = px.bar(grouped, x='Lead time range1', y='counts', color='Rate Name',color_discrete_map=color_scale, barmode='stack')
                            st.plotly_chart(fig,use_container_width=True)
                        with med :
                            grouped = filtered_df.groupby(['Lead time range1', 'utm_medium']).size().reset_index(name='counts')
                            fig = px.bar(grouped, x='Lead time range1', y='counts', color='utm_medium',color_discrete_map=color_scale, barmode='stack')
                            st.plotly_chart(fig,use_container_width=True)     
                        with rt :
                            grouped = filtered_df.groupby(['Lead time range1', 'Room type']).size().reset_index(name='counts')
                            fig = px.bar(grouped, x='Lead time range1', y='counts', color='Room type',color_discrete_map=color_scale, barmode='stack')
                            st.plotly_chart(fig,use_container_width=True) 
                    with l3:
                        ch,rn,med,rt = st.tabs(['Count LT by Source','Count booking by Rate name','Count LT by utm medium','Count LT by Room type'])
                        with ch:
                            grouped = filtered_df.groupby(['Lead Time', 'Booking Source']).size().reset_index(name='counts')
                            fig = px.bar(grouped, x='Lead Time', y='counts', color='Booking Source',color_discrete_map=color_scale, barmode='stack')
                            st.plotly_chart(fig,use_container_width=True)
                        with rn :
                            grouped = filtered_df.groupby(['Lead Time', 'Rate Name']).size().reset_index(name='counts')
                            fig = px.bar(grouped, x='Lead Time', y='counts', color='Rate Name',color_discrete_map=color_scale, barmode='stack')
                            st.plotly_chart(fig,use_container_width=True)
                        with med :
                            grouped = filtered_df.groupby(['Lead Time', 'utm_medium']).size().reset_index(name='counts')
                            fig = px.bar(grouped, x='Lead Time', y='counts', color='utm_medium',color_discrete_map=color_scale, barmode='stack')
                            st.plotly_chart(fig,use_container_width=True)     
                        with rt :
                            grouped = filtered_df.groupby(['Lead Time', 'Room type']).size().reset_index(name='counts')
                            fig = px.bar(grouped, x='Lead Time', y='counts', color='Room type',color_discrete_map=color_scale, barmode='stack')
                            st.plotly_chart(fig,use_container_width=True) 


                tab1, tab2, tab3 ,tab4, tab5 , tab6 ,tab7,t0,tab8 = st.tabs(["Average", "Median", "Statistic",'Data'
                                                                ,'Bar Chart','Room roomnight by channel'
                                                                ,'Room revenue by channel','Room type by channel','etc.'])
                with tab1:
                    col0, col1, col2, col4 = st.columns(4)
                    filtered_df['total ADR'] = filtered_df["ADR"]*filtered_df["LOS"]*filtered_df["Quantity"]
                    col0.metric('**Revenue**',f'{round(filtered_df["total ADR"].sum(),4)}')
                    col4.metric('**ADR**',f'{round(filtered_df["ADR"].mean(),4)}',)
                    col1.metric("**A.LT**", f'{round(filtered_df["Lead Time"].mean(),4)}')
                    col2.metric("**A.LOS**", f'{round(filtered_df["LOS"].mean(),4)}')
                with tab2:
                    col1, col2, col3= st.columns(3)
                    col1.metric('ADR',f'{round(filtered_df["ADR"].median(),4)}')
                    col2.metric("A.LT", f'{round(filtered_df["Lead Time"].median(),4)}')
                    col3.metric("A.LOS", f'{round(filtered_df["LOS"].median(),4)}')
                with tab3:
                    st.write(filtered_df.describe())
                with tab4:
                    st.write(filtered_df)
                with tab5:
                    tab11, tab12, tab13, tab14 = st.tabs(['A.LT','A.LOS','A.RN','ADR by month'])
                    with tab14:
                        month_order = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
                        mean_adr_by_month = filtered_df.groupby(['Room type', filtered_df['Booking Date'].dt.month_name()])['ADR'].mean().reset_index()
                        mean_adr_by_month['Booking Date'] = pd.Categorical(mean_adr_by_month['Booking Date'], categories=month_order)

                        bar_chart = px.bar(mean_adr_by_month, x='Booking Date', y='ADR', color='Room type',category_orders={'Booking Date': month_order},
                            text='ADR')
                        bar_chart.update_traces(texttemplate='%{text:.2f}', textposition='auto')
                        st.plotly_chart(bar_chart, use_container_width=True)
                    with tab11:
                        month_order = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
                        mean_adr_by_month = filtered_df.groupby(['Room type', filtered_df['Booking Date'].dt.month_name()])['Lead Time'].mean().reset_index()
                        mean_adr_by_month['Booking Date'] = pd.Categorical(mean_adr_by_month['Booking Date'], categories=month_order)

                        bar_chart = px.bar(mean_adr_by_month, x='Booking Date', y='Lead Time', color='Room type',category_orders={'Booking Date': month_order},
                            text='Lead Time')
                        bar_chart.update_traces(texttemplate='%{text:.2f}', textposition='auto')
                        st.plotly_chart(bar_chart, use_container_width=True)
                    with tab12:
                        month_order = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
                        mean_adr_by_month = filtered_df.groupby(['Room type', filtered_df['Booking Date'].dt.month_name()])['LOS'].mean().reset_index()
                        mean_adr_by_month['Booking Date'] = pd.Categorical(mean_adr_by_month['Booking Date'], categories=month_order)

                        bar_chart = px.bar(mean_adr_by_month, x='Booking Date', y='LOS', color='Room type',category_orders={'Booking Date': month_order},
                            text='LOS')
                        bar_chart.update_traces(texttemplate='%{text:.2f}', textposition='auto')
                        st.plotly_chart(bar_chart, use_container_width=True)
                    with tab13:
                        month_order = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
                        mean_adr_by_month = filtered_df.groupby(['Room type', filtered_df['Booking Date'].dt.month_name()])['RN'].mean().reset_index()
                        mean_adr_by_month['Booking Date'] = pd.Categorical(mean_adr_by_month['Booking Date'], categories=month_order)

                        bar_chart = px.bar(mean_adr_by_month, x='Booking Date', y='RN', color='Room type',category_orders={'Booking Date': month_order},
                            text='RN')
                        bar_chart.update_traces(texttemplate='%{text:.2f}', textposition='auto')
                        st.plotly_chart(bar_chart, use_container_width=True)

                with tab6:
                    counts = filtered_df[['Booking Source', 'Room type','RN']].groupby(['Booking Source', 'Room type']).sum().reset_index()
                    fig = px.treemap(counts, path=['Booking Source', 'Room type','RN'], values='RN', color='RN',color_continuous_scale='YlOrRd')
                    st.plotly_chart(fig,use_container_width=True)
                with tab7:
                    counts = filtered_df[['Booking Source', 'Room type','ADR']].groupby(['Booking Source', 'Room type']).sum().reset_index()
                    fig = px.treemap(counts, path=['Booking Source', 'Room type','ADR'], values='ADR', color='ADR',color_continuous_scale='YlOrRd')
                    st.plotly_chart(fig,use_container_width=True)
                with t0:
                    counts = filtered_df[['Booking Source', 'Room type']].groupby(['Booking Source', 'Room type']).size().reset_index(name='Count')
                    total_count = counts['Count'].sum()
                    fig = px.treemap(counts, path=['Booking Source', 'Room type'], values='Count', color='Count',color_continuous_scale='YlOrRd')
                    st.plotly_chart(fig,use_container_width=True)
                with tab8:
                    t1,t2,t3,t4,t5,t6,t7,t8 = st.tabs(['Gender','Nationality','Booking Location'
                                                    ,'View Language','View Currency','Booking Status'
                                                    ,'Payment Gateway','Payment Scheme'])
                    with t1:
                        counts = filtered_df['Gender'].value_counts()
                        total = counts.sum()
                        percentages = counts / total * 100
                        fig = go.Figure(go.Bar(
                            x=percentages.index,
                            y=percentages,
                            text=percentages.apply(lambda x: f'{x:.0f}%'),
                            ))
                        st.plotly_chart(fig,use_container_width=True)
                    with t2:
                        counts = filtered_df['iso_alpha1'].value_counts()
                        total = counts.sum()
                        percentages = counts / total * 100
                        fig = go.Figure(go.Bar(
                            x=percentages.index,
                            y=percentages,
                            text=percentages.apply(lambda x: f'{x:.0f}%'),
                            ))
                        st.plotly_chart(fig,use_container_width=True)
                    with t3:
                        counts = filtered_df['iso_alpha'].value_counts()
                        total = counts.sum()
                        percentages = counts / total * 100
                        fig = go.Figure(go.Bar(
                            x=percentages.index,
                            y=percentages,
                            text=percentages.apply(lambda x: f'{x:.0f}%'),
                            ))
                        st.plotly_chart(fig,use_container_width=True)
                    with t4:
                        counts = filtered_df['View Language'].value_counts()
                        total = counts.sum()
                        percentages = counts / total * 100
                        fig = go.Figure(go.Bar(
                            x=percentages.index,
                            y=percentages,
                            text=percentages.apply(lambda x: f'{x:.0f}%'),
                            ))
                        st.plotly_chart(fig,use_container_width=True)
                    with t5:
                        counts = filtered_df['View Currency'].value_counts()
                        total = counts.sum()
                        percentages = counts / total * 100
                        fig = go.Figure(go.Bar(
                            x=percentages.index,
                            y=percentages,
                            text=percentages.apply(lambda x: f'{x:.0f}%'),
                            ))
                        st.plotly_chart(fig,use_container_width=True)
                    with t6:
                        counts = filtered_df['Booking Status'].value_counts()
                        total = counts.sum()
                        percentages = counts / total * 100
                        fig = go.Figure(go.Bar(
                            x=percentages.index,
                            y=percentages,
                            text=percentages.apply(lambda x: f'{x:.0f}%'),
                            ))
                        st.plotly_chart(fig,use_container_width=True)
                    with t7:
                        counts = filtered_df['Payment Gateway'].value_counts()
                        total = counts.sum()
                        percentages = counts / total * 100
                        fig = go.Figure(go.Bar(
                            x=percentages.index,
                            y=percentages,
                            text=percentages.apply(lambda x: f'{x:.0f}%'),
                            ))
                        st.plotly_chart(fig,use_container_width=True)
                    with t8:
                        counts = filtered_df['Payment Scheme'].value_counts()
                        total = counts.sum()
                        percentages = counts / total * 100
                        fig = go.Figure(go.Bar(
                            x=percentages.index,
                            y=percentages,
                            text=percentages.apply(lambda x: f'{x:.0f}%'),
                            ))
                        st.plotly_chart(fig,use_container_width=True)

                filtered_df['Booking Date'] = pd.to_datetime(filtered_df['Booking Date'])
                filtered_df['Day Name'] = filtered_df['Booking Date'].dt.strftime('%A')
                filtered_df['Week of Year'] = filtered_df['Booking Date'].dt.isocalendar().week


                col1, col2 = st.columns(2)
                with col1:
                    st.markdown('**count Booking in week of Year (calendar)**')
                    pt = filtered_df.pivot_table(index='Week of Year', columns='Day Name', aggfunc='size', fill_value=0)
                    if set(['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']).issubset(filtered_df['Day Name'].unique()):
                        pt = filtered_df.pivot_table(index='Week of Year', columns='Day Name', aggfunc='size', fill_value=0)
                        pt = pt[['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']]
                        st.write(pt.style.background_gradient(cmap='coolwarm', axis=1))
                    else:
                        st.write('Not enough data to create a pivot table')

                with col2:
                    filtered_df1 =filtered_df[['Booking Date','RN']]
                    df_grouped = filtered_df1.groupby('Booking Date').sum().reset_index()
                    pivot_df = df_grouped.pivot_table(values='RN'
                                            , index=df_grouped['Booking Date'].dt.isocalendar().week
                                            , columns=df_grouped['Booking Date'].dt.day_name(), aggfunc='sum', fill_value=0)
                    st.markdown('**count Roomnight in week of Year (calendar)**')
                    if set(['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']).issubset(filtered_df['Day Name'].unique()):
                        pt = pivot_df[['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']]
                        st.write(pt.style.background_gradient(cmap='coolwarm', axis=1))
                    else:
                        st.write('Not enough data to create a pivot table')

                t0,tb,tLT,tLOS = st.tabs(['**LMvsTM**','**Pivot by Booked**','**Pivot by LT**','**Pivot by LOS**'])
                with t0:
                    st.markdown('**LMvsTM**')
                    book_status = all2['Booking Status'].unique()

                    selected_bs = st.multiselect('Select Booking status. ', book_status, default=[], key='books_select')
                    if selected_bs:
                        filtered_df = filtered_df[filtered_df['Booking Status'].isin(selected_bs)]
                    else:
                        filtered_df = filtered_df
                    t1,t_reatecode,t_acce,t_utm_content= st.tabs(['Total revenue (Room type)','Total revenue by rate code','Total revenue by Access code','Total revenue by utm'])
                    with t1: 
                            t1,t2 = st.tabs(['sum','count'])
                            with t1:
                                col1,col2 = st.columns(2)
                                month_order = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
                                mean_adr_by_month = filtered_df.groupby(['Room type', filtered_df['Booking Date'].dt.month_name()])['Total Revenue'].sum().reset_index()
                                mean_adr_by_month['Booking Date'] = pd.Categorical(mean_adr_by_month['Booking Date'], categories=month_order)

                                bar_chart = px.bar(mean_adr_by_month, x='Total Revenue', y='Booking Date', color='Room type', category_orders={'Booking Date': month_order},
                                                text='Total Revenue', orientation='h')
                                bar_chart.update_traces(texttemplate='%{text:.2f}', textposition='auto')
                                bar_chart.update_layout(legend=dict(orientation="h",yanchor="bottom",y=1.02,xanchor="right",x=1))
                                col1.plotly_chart(bar_chart, use_container_width=True)
                                month_order = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
                                mean_adr_by_month = filtered_df.groupby([filtered_df['Booking Date'].dt.month_name()])['Total Revenue'].sum().reset_index()
                                mean_adr_by_month['Booking Date'] = pd.Categorical(mean_adr_by_month['Booking Date'], categories=month_order)

                                bar_chart = px.bar(mean_adr_by_month, x='Total Revenue', y='Booking Date', category_orders={'Booking Date': month_order},
                                                text='Total Revenue', orientation='h')
                                bar_chart.update_traces(texttemplate='%{text:.2f}', textposition='auto')
                                bar_chart.update_layout(legend=dict(orientation="h",yanchor="bottom",y=1.02,xanchor="right",x=1))
                                col2.plotly_chart(bar_chart, use_container_width=True)
                            with t2:
                                col1,col2 = st.columns(2)
                                month_order = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
                                count_roomtype_by_month = filtered_df.groupby(['Room type', filtered_df['Booking Date'].dt.month_name()]).size().reset_index(name='Count')
                                count_roomtype_by_month['Booking Date'] = pd.Categorical(count_roomtype_by_month['Booking Date'], categories=month_order)

                                bar_chart = px.bar(count_roomtype_by_month, x='Count', y='Booking Date', color='Room type', category_orders={'Booking Date': month_order},
                                                text='Count')
                                bar_chart.update_traces(texttemplate='%{text}', textposition='auto')
                                bar_chart.update_layout(legend=dict(orientation="h",yanchor="bottom",y=1.02,xanchor="right",x=1))
                                col1.plotly_chart(bar_chart, use_container_width=True)
                                month_order = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
                                count_roomtype_by_month = filtered_df.groupby([filtered_df['Booking Date'].dt.month_name()]).size().reset_index(name='Count')
                                count_roomtype_by_month['Booking Date'] = pd.Categorical(count_roomtype_by_month['Booking Date'], categories=month_order)

                                bar_chart = px.bar(count_roomtype_by_month, x='Count', y='Booking Date', category_orders={'Booking Date': month_order},
                                                text='Count')
                                bar_chart.update_traces(texttemplate='%{text}', textposition='auto')
                                col2.plotly_chart(bar_chart, use_container_width=True)
                    with t_reatecode:
                            t11,t22,t33 = st.tabs(['sum ratecode','count ratecode','Pie chart'])
                            with t11:
                                col1,col2 = st.columns(2)
                                month_order = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
                                mean_adr_by_month = filtered_df.groupby(['Rate Name', filtered_df['Booking Date'].dt.month_name()])['Total Revenue'].sum().reset_index()
                                mean_adr_by_month['Booking Date'] = pd.Categorical(mean_adr_by_month['Booking Date'], categories=month_order)
                                bar_chart = px.bar(mean_adr_by_month, x='Total Revenue', y='Booking Date', color='Rate Name',category_orders={'Booking Date': month_order},
                                    text='Total Revenue')
                                bar_chart.update_traces(texttemplate='%{text:.2f}', textposition='auto')
                                bar_chart.update_layout(legend=dict(orientation="h",yanchor="bottom",y=1.02,xanchor="right",x=1))
                                col1.plotly_chart(bar_chart, use_container_width=True)
                                month_order = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
                                mean_adr_by_month = filtered_df.groupby([filtered_df['Booking Date'].dt.month_name()])['Total Revenue'].sum().reset_index()
                                mean_adr_by_month['Booking Date'] = pd.Categorical(mean_adr_by_month['Booking Date'], categories=month_order)
                                bar_chart = px.bar(mean_adr_by_month, x='Total Revenue', y='Booking Date',category_orders={'Booking Date': month_order},
                                    text='Total Revenue')
                                bar_chart.update_traces(texttemplate='%{text:.2f}', textposition='auto')
                                bar_chart.update_layout(legend=dict(orientation="h",yanchor="bottom",y=1.02,xanchor="right",x=1))
                                col2.plotly_chart(bar_chart, use_container_width=True)
                            with t22:
                                col1,col2 = st.columns(2)
                                month_order = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
                                count_roomtype_by_month = filtered_df.groupby(['Rate Name', filtered_df['Booking Date'].dt.month_name()]).size().reset_index(name='Count')
                                count_roomtype_by_month['Booking Date'] = pd.Categorical(count_roomtype_by_month['Booking Date'], categories=month_order)

                                bar_chart = px.bar(count_roomtype_by_month, x='Count', y='Booking Date', color='Rate Name', category_orders={'Booking Date': month_order},
                                                text='Count')
                                bar_chart.update_traces(texttemplate='%{text}', textposition='auto')
                                bar_chart.update_layout(legend=dict(orientation="h",yanchor="bottom",y=1.02,xanchor="right",x=1))
                                col1.plotly_chart(bar_chart, use_container_width=True)
                                month_order = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
                                count_roomtype_by_month = filtered_df.groupby([filtered_df['Booking Date'].dt.month_name()]).size().reset_index(name='Count')
                                count_roomtype_by_month['Booking Date'] = pd.Categorical(count_roomtype_by_month['Booking Date'], categories=month_order)

                                bar_chart = px.bar(count_roomtype_by_month, x='Count', y='Booking Date', category_orders={'Booking Date': month_order},
                                                text='Count')
                                bar_chart.update_traces(texttemplate='%{text}', textposition='auto')
                                bar_chart.update_layout(legend=dict(orientation="h",yanchor="bottom",y=1.02,xanchor="right",x=1))
                                col2.plotly_chart(bar_chart, use_container_width=True)
                            with t33:
                                los_counts = filtered_df['Rate Name'].value_counts().reset_index()
                                los_counts.columns = ['Rate Name', 'Count']
                                los_counts = los_counts.sort_values('Rate Name')
                                fig = px.pie(los_counts, values='Count', names='Rate Name', 
                                    title='Rate Name Distribution',
                                    hole=0.4)
                                fig.update_traces(textposition='outside', textinfo='percent+label')
                                st.plotly_chart(fig,use_container_width=True)
                    with t_acce:
                            t11,t22,t33 = st.tabs(['sum Access code','count Access code','Pie chart'])
                            with t11:
                                col1,col2 = st.columns(2)
                                month_order = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
                                mean_adr_by_month = filtered_df.groupby(['Access Code', filtered_df['Booking Date'].dt.month_name()])['Total Revenue'].sum().reset_index()
                                mean_adr_by_month['Booking Date'] = pd.Categorical(mean_adr_by_month['Booking Date'], categories=month_order)
                                bar_chart = px.bar(mean_adr_by_month, x='Total Revenue', y='Booking Date', color='Access Code',category_orders={'Booking Date': month_order},
                                    text='Total Revenue')
                                bar_chart.update_traces(texttemplate='%{text:.2f}', textposition='auto')
                                bar_chart.update_layout(legend=dict(orientation="h",yanchor="bottom",y=1.02,xanchor="right",x=1))
                                col1.plotly_chart(bar_chart, use_container_width=True)
                                month_order = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
                                mean_adr_by_month = filtered_df.groupby([filtered_df['Booking Date'].dt.month_name()])['Total Revenue'].sum().reset_index()
                                mean_adr_by_month['Booking Date'] = pd.Categorical(mean_adr_by_month['Booking Date'], categories=month_order)
                                bar_chart = px.bar(mean_adr_by_month, x='Total Revenue', y='Booking Date',category_orders={'Booking Date': month_order},
                                    text='Total Revenue')
                                bar_chart.update_traces(texttemplate='%{text:.2f}', textposition='auto')
                                bar_chart.update_layout(legend=dict(orientation="h",yanchor="bottom",y=1.02,xanchor="right",x=1))
                                col2.plotly_chart(bar_chart, use_container_width=True)
                            with t22:
                                col1,col2 = st.columns(2)
                                month_order = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
                                count_roomtype_by_month = filtered_df.groupby(['Access Code', filtered_df['Booking Date'].dt.month_name()]).size().reset_index(name='Count')
                                count_roomtype_by_month['Booking Date'] = pd.Categorical(count_roomtype_by_month['Booking Date'], categories=month_order)

                                bar_chart = px.bar(count_roomtype_by_month, x='Count', y='Booking Date', color='Access Code', category_orders={'Booking Date': month_order},
                                                text='Count')
                                bar_chart.update_traces(texttemplate='%{text}', textposition='auto')
                                bar_chart.update_layout(legend=dict(orientation="h",yanchor="bottom",y=1.02,xanchor="right",x=1))
                                col1.plotly_chart(bar_chart, use_container_width=True)
                                month_order = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
                                count_roomtype_by_month = filtered_df.groupby([filtered_df['Booking Date'].dt.month_name()]).size().reset_index(name='Count')
                                count_roomtype_by_month['Booking Date'] = pd.Categorical(count_roomtype_by_month['Booking Date'], categories=month_order)

                                bar_chart = px.bar(count_roomtype_by_month, x='Count', y='Booking Date', category_orders={'Booking Date': month_order},
                                                text='Count')
                                bar_chart.update_traces(texttemplate='%{text}', textposition='auto')
                                bar_chart.update_layout(legend=dict(orientation="h",yanchor="bottom",y=1.02,xanchor="right",x=1))
                                col2.plotly_chart(bar_chart, use_container_width=True)
                            with t33:
                                los_counts = filtered_df['Access Code'].value_counts().reset_index()
                                los_counts.columns = ['Access Code', 'Count']
                                los_counts = los_counts.sort_values('Access Code')
                                fig = px.pie(los_counts, values='Count', names='Access Code', 
                                    title='Access Code Distribution',
                                    hole=0.4)
                                fig.update_traces(textposition='outside', textinfo='percent+label')
                                st.plotly_chart(fig,use_container_width=True)
                    with t_utm_content:
                            cont,source,medium,campag = st.tabs(['utm content','utm source','utm medium','utm campaign'])
                            with cont:
                                t11,t22,t33 = st.tabs(['sum utm_content','count utm_content','Pie chart'])
                                with t11:
                                    col1,col2 = st.columns(2)
                                    month_order = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
                                    mean_adr_by_month = filtered_df.groupby(['utm_content', filtered_df['Booking Date'].dt.month_name()])['Total Revenue'].sum().reset_index()
                                    mean_adr_by_month['Booking Date'] = pd.Categorical(mean_adr_by_month['Booking Date'], categories=month_order)
                                    bar_chart = px.bar(mean_adr_by_month, x='Total Revenue', y='Booking Date', color='utm_content',category_orders={'Booking Date': month_order},
                                        text='Total Revenue')
                                    bar_chart.update_traces(texttemplate='%{text:.2f}', textposition='auto')
                                    bar_chart.update_layout(legend=dict(orientation="h",yanchor="bottom",y=1.02,xanchor="right",x=1))
                                    col1.plotly_chart(bar_chart, use_container_width=True)
                                    month_order = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
                                    mean_adr_by_month = filtered_df.groupby([filtered_df['Booking Date'].dt.month_name()])['Total Revenue'].sum().reset_index()
                                    mean_adr_by_month['Booking Date'] = pd.Categorical(mean_adr_by_month['Booking Date'], categories=month_order)
                                    bar_chart = px.bar(mean_adr_by_month, x='Total Revenue', y='Booking Date',category_orders={'Booking Date': month_order},
                                        text='Total Revenue')
                                    bar_chart.update_traces(texttemplate='%{text:.2f}', textposition='auto')
                                    bar_chart.update_layout(legend=dict(orientation="h",yanchor="bottom",y=1.02,xanchor="right",x=1))
                                    col2.plotly_chart(bar_chart, use_container_width=True)
                                with t22:
                                    col1,col2 = st.columns(2)
                                    month_order = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
                                    count_roomtype_by_month = filtered_df.groupby(['utm_content', filtered_df['Booking Date'].dt.month_name()]).size().reset_index(name='Count')
                                    count_roomtype_by_month['Booking Date'] = pd.Categorical(count_roomtype_by_month['Booking Date'], categories=month_order)

                                    bar_chart = px.bar(count_roomtype_by_month, x='Count', y='Booking Date', color='utm_content', category_orders={'Booking Date': month_order},
                                                    text='Count')
                                    bar_chart.update_traces(texttemplate='%{text}', textposition='auto')
                                    bar_chart.update_layout(legend=dict(orientation="h",yanchor="bottom",y=1.02,xanchor="right",x=1))
                                    col1.plotly_chart(bar_chart, use_container_width=True)
                                    month_order = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
                                    count_roomtype_by_month = filtered_df.groupby([filtered_df['Booking Date'].dt.month_name()]).size().reset_index(name='Count')
                                    count_roomtype_by_month['Booking Date'] = pd.Categorical(count_roomtype_by_month['Booking Date'], categories=month_order)

                                    bar_chart = px.bar(count_roomtype_by_month, x='Count', y='Booking Date', category_orders={'Booking Date': month_order},
                                                    text='Count')
                                    bar_chart.update_traces(texttemplate='%{text}', textposition='auto')
                                    bar_chart.update_layout(legend=dict(orientation="h",yanchor="bottom",y=1.02,xanchor="right",x=1))
                                    col2.plotly_chart(bar_chart, use_container_width=True)
                                with t33:
                                    los_counts = filtered_df['utm_content'].value_counts().reset_index()
                                    los_counts.columns = ['utm_content', 'Count']
                                    los_counts = los_counts.sort_values('utm_content')
                                    fig = px.pie(los_counts, values='Count', names='utm_content', 
                                        title='utm_content Distribution',
                                        hole=0.4)
                                    fig.update_traces(textposition='inside', textinfo='percent+label')
                                    st.plotly_chart(fig,use_container_width=True)
                            with source:
                                t11,t22,t33 = st.tabs(['sum utm_source','count utm_source','Pie chart'])
                                with t11:
                                    col1,col2 = st.columns(2)
                                    month_order = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
                                    mean_adr_by_month = filtered_df.groupby(['utm_source', filtered_df['Booking Date'].dt.month_name()])['Total Revenue'].sum().reset_index()
                                    mean_adr_by_month['Booking Date'] = pd.Categorical(mean_adr_by_month['Booking Date'], categories=month_order)
                                    bar_chart = px.bar(mean_adr_by_month, x='Total Revenue', y='Booking Date', color='utm_source',category_orders={'Booking Date': month_order},
                                        text='Total Revenue')
                                    bar_chart.update_traces(texttemplate='%{text:.2f}', textposition='auto')
                                    bar_chart.update_layout(legend=dict(orientation="h",yanchor="bottom",y=1.02,xanchor="right",x=1))
                                    col1.plotly_chart(bar_chart, use_container_width=True)
                                    month_order = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
                                    mean_adr_by_month = filtered_df.groupby([filtered_df['Booking Date'].dt.month_name()])['Total Revenue'].sum().reset_index()
                                    mean_adr_by_month['Booking Date'] = pd.Categorical(mean_adr_by_month['Booking Date'], categories=month_order)
                                    bar_chart = px.bar(mean_adr_by_month, x='Total Revenue', y='Booking Date',category_orders={'Booking Date': month_order},
                                        text='Total Revenue')
                                    bar_chart.update_traces(texttemplate='%{text:.2f}', textposition='auto')
                                    bar_chart.update_layout(legend=dict(orientation="h",yanchor="bottom",y=1.02,xanchor="right",x=1))
                                    col2.plotly_chart(bar_chart, use_container_width=True)
                                with t22:
                                    col1,col2 = st.columns(2)
                                    month_order = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
                                    count_roomtype_by_month = filtered_df.groupby(['utm_source', filtered_df['Booking Date'].dt.month_name()]).size().reset_index(name='Count')
                                    count_roomtype_by_month['Booking Date'] = pd.Categorical(count_roomtype_by_month['Booking Date'], categories=month_order)

                                    bar_chart = px.bar(count_roomtype_by_month, x='Count', y='Booking Date', color='utm_source', category_orders={'Booking Date': month_order},
                                                    text='Count')
                                    bar_chart.update_traces(texttemplate='%{text}', textposition='auto')
                                    bar_chart.update_layout(legend=dict(orientation="h",yanchor="bottom",y=1.02,xanchor="right",x=1))
                                    col1.plotly_chart(bar_chart, use_container_width=True)
                                    month_order = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
                                    count_roomtype_by_month = filtered_df.groupby([filtered_df['Booking Date'].dt.month_name()]).size().reset_index(name='Count')
                                    count_roomtype_by_month['Booking Date'] = pd.Categorical(count_roomtype_by_month['Booking Date'], categories=month_order)

                                    bar_chart = px.bar(count_roomtype_by_month, x='Count', y='Booking Date', category_orders={'Booking Date': month_order},
                                                    text='Count')
                                    bar_chart.update_traces(texttemplate='%{text}', textposition='auto')
                                    bar_chart.update_layout(legend=dict(orientation="h",yanchor="bottom",y=1.02,xanchor="right",x=1))
                                    col2.plotly_chart(bar_chart, use_container_width=True)
                                with t33:
                                    los_counts = filtered_df['utm_source'].value_counts().reset_index()
                                    los_counts.columns = ['utm_source', 'Count']
                                    los_counts = los_counts.sort_values('utm_source')
                                    fig = px.pie(los_counts, values='Count', names='utm_source', 
                                        title='utm_source Distribution',
                                        hole=0.4)
                                    fig.update_traces(textposition='inside', textinfo='percent+label')
                                    st.plotly_chart(fig,use_container_width=True)
                            with medium:
                                t11,t22,t33 = st.tabs(['sum utm_medium','count utm_medium','Pie chart'])
                                with t11:
                                    col1,col2 = st.columns(2)
                                    month_order = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
                                    mean_adr_by_month = filtered_df.groupby(['utm_medium', filtered_df['Booking Date'].dt.month_name()])['Total Revenue'].sum().reset_index()
                                    mean_adr_by_month['Booking Date'] = pd.Categorical(mean_adr_by_month['Booking Date'], categories=month_order)
                                    bar_chart = px.bar(mean_adr_by_month, x='Total Revenue', y='Booking Date', color='utm_medium',category_orders={'Booking Date': month_order},
                                        text='Total Revenue')
                                    bar_chart.update_traces(texttemplate='%{text:.2f}', textposition='auto')
                                    bar_chart.update_layout(legend=dict(orientation="h",yanchor="bottom",y=1.02,xanchor="right",x=1))
                                    col1.plotly_chart(bar_chart, use_container_width=True)
                                    month_order = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
                                    mean_adr_by_month = filtered_df.groupby([filtered_df['Booking Date'].dt.month_name()])['Total Revenue'].sum().reset_index()
                                    mean_adr_by_month['Booking Date'] = pd.Categorical(mean_adr_by_month['Booking Date'], categories=month_order)
                                    bar_chart = px.bar(mean_adr_by_month, x='Total Revenue', y='Booking Date',category_orders={'Booking Date': month_order},
                                        text='Total Revenue')
                                    bar_chart.update_traces(texttemplate='%{text:.2f}', textposition='auto')
                                    bar_chart.update_layout(legend=dict(orientation="h",yanchor="bottom",y=1.02,xanchor="right",x=1))
                                    col2.plotly_chart(bar_chart, use_container_width=True)
                                with t22:
                                    col1,col2 = st.columns(2)
                                    month_order = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
                                    count_roomtype_by_month = filtered_df.groupby(['utm_medium', filtered_df['Booking Date'].dt.month_name()]).size().reset_index(name='Count')
                                    count_roomtype_by_month['Booking Date'] = pd.Categorical(count_roomtype_by_month['Booking Date'], categories=month_order)

                                    bar_chart = px.bar(count_roomtype_by_month, x='Count', y='Booking Date', color='utm_medium', category_orders={'Booking Date': month_order},
                                                    text='Count')
                                    bar_chart.update_traces(texttemplate='%{text}', textposition='auto')
                                    bar_chart.update_layout(legend=dict(orientation="h",yanchor="bottom",y=1.02,xanchor="right",x=1))
                                    col1.plotly_chart(bar_chart, use_container_width=True)
                                    month_order = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
                                    count_roomtype_by_month = filtered_df.groupby([filtered_df['Booking Date'].dt.month_name()]).size().reset_index(name='Count')
                                    count_roomtype_by_month['Booking Date'] = pd.Categorical(count_roomtype_by_month['Booking Date'], categories=month_order)

                                    bar_chart = px.bar(count_roomtype_by_month, x='Count', y='Booking Date', category_orders={'Booking Date': month_order},
                                                    text='Count')
                                    bar_chart.update_traces(texttemplate='%{text}', textposition='auto')
                                    bar_chart.update_layout(legend=dict(orientation="h",yanchor="bottom",y=1.02,xanchor="right",x=1))
                                    col2.plotly_chart(bar_chart, use_container_width=True)
                                with t33:
                                    los_counts = filtered_df['utm_medium'].value_counts().reset_index()
                                    los_counts.columns = ['utm_medium', 'Count']
                                    los_counts = los_counts.sort_values('utm_medium')
                                    fig = px.pie(los_counts, values='Count', names='utm_medium', 
                                        title='utm_medium Distribution',
                                        hole=0.4)
                                    fig.update_traces(textposition='inside', textinfo='percent+label')
                                    st.plotly_chart(fig,use_container_width=True)
                            with campag:
                                t11,t22,t33 = st.tabs(['sum campaign','count campaign','Pie chart'])
                                with t11:
                                    col1,col2 = st.columns(2)
                                    month_order = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
                                    mean_adr_by_month = filtered_df.groupby(['Campaign', filtered_df['Booking Date'].dt.month_name()])['Total Revenue'].sum().reset_index()
                                    mean_adr_by_month['Booking Date'] = pd.Categorical(mean_adr_by_month['Booking Date'], categories=month_order)
                                    bar_chart = px.bar(mean_adr_by_month, x='Total Revenue', y='Booking Date', color='Campaign',category_orders={'Booking Date': month_order},
                                        text='Total Revenue')
                                    bar_chart.update_traces(texttemplate='%{text:.2f}', textposition='auto')
                                    bar_chart.update_layout(legend=dict(orientation="h",yanchor="bottom",y=1.02,xanchor="right",x=1))
                                    col1.plotly_chart(bar_chart, use_container_width=True)
                                    month_order = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
                                    mean_adr_by_month = filtered_df.groupby([filtered_df['Booking Date'].dt.month_name()])['Total Revenue'].sum().reset_index()
                                    mean_adr_by_month['Booking Date'] = pd.Categorical(mean_adr_by_month['Booking Date'], categories=month_order)
                                    bar_chart = px.bar(mean_adr_by_month, x='Total Revenue', y='Booking Date',category_orders={'Booking Date': month_order},
                                        text='Total Revenue')
                                    bar_chart.update_traces(texttemplate='%{text:.2f}', textposition='auto')
                                    bar_chart.update_layout(legend=dict(orientation="h",yanchor="bottom",y=1.02,xanchor="right",x=1))
                                    col2.plotly_chart(bar_chart, use_container_width=True)
                                with t22:
                                    col1,col2 = st.columns(2)
                                    month_order = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
                                    count_roomtype_by_month = filtered_df.groupby(['Campaign', filtered_df['Booking Date'].dt.month_name()]).size().reset_index(name='Count')
                                    count_roomtype_by_month['Booking Date'] = pd.Categorical(count_roomtype_by_month['Booking Date'], categories=month_order)

                                    bar_chart = px.bar(count_roomtype_by_month, x='Count', y='Booking Date', color='Campaign', category_orders={'Booking Date': month_order},
                                                    text='Count')
                                    bar_chart.update_traces(texttemplate='%{text}', textposition='auto')
                                    bar_chart.update_layout(legend=dict(orientation="h",yanchor="bottom",y=1.02,xanchor="right",x=1))
                                    col1.plotly_chart(bar_chart, use_container_width=True)
                                    month_order = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
                                    count_roomtype_by_month = filtered_df.groupby([filtered_df['Booking Date'].dt.month_name()]).size().reset_index(name='Count')
                                    count_roomtype_by_month['Booking Date'] = pd.Categorical(count_roomtype_by_month['Booking Date'], categories=month_order)

                                    bar_chart = px.bar(count_roomtype_by_month, x='Count', y='Booking Date', category_orders={'Booking Date': month_order},
                                                    text='Count')
                                    bar_chart.update_traces(texttemplate='%{text}', textposition='auto')
                                    bar_chart.update_layout(legend=dict(orientation="h",yanchor="bottom",y=1.02,xanchor="right",x=1))
                                    col2.plotly_chart(bar_chart, use_container_width=True)
                                with t33:
                                    los_counts = filtered_df['Campaign'].value_counts().reset_index()
                                    los_counts.columns = ['Campaign', 'Count']
                                    los_counts = los_counts.sort_values('Campaign')
                                    fig = px.pie(los_counts, values='Count', names='Campaign', 
                                        title='Campaign Distribution',
                                        hole=0.4)
                                    fig.update_traces(textposition='inside', textinfo='percent+label')
                                    st.plotly_chart(fig,use_container_width=True)

                with tb:
                    st.markdown('**Pivot table by Booked**')
                    t1,t2,t3,t4 = st.tabs(['ADR','LT','LOS','RN'])
                    with t1:
                        col1, col2 = st.columns(2)
                        #filtered_df_pi = pd.pivot_table(filtered_df, index='Booked',values=['ADR'])
                        col1.markdown('Average ADR by booked and Room Type')
                        #st.bar_chart(filtered_df_pi)
                        adr_avg = filtered_df.groupby(['Booking Date', 'Room type'])['ADR'].mean().reset_index()
                        fig = px.bar(adr_avg, x='Booking Date', y='ADR', color='Room type',text_auto=True)
                        fig.update_layout(legend=dict(orientation="h",yanchor="bottom",y=1.02,xanchor="right",x=1))
                        col1.plotly_chart(fig, use_container_width=True)
                        #filtered_df_pi = pd.pivot_table(filtered_df, index='Booked',values=['ADR'])
                        col2.markdown('Average ADR by booked')
                        #st.bar_chart(filtered_df_pi)
                        adr_avg = filtered_df.groupby(['Booking Date'])['ADR'].mean().reset_index()
                        fig = px.bar(adr_avg, x='Booking Date', y='ADR',text_auto=True)
                        col2.plotly_chart(fig, use_container_width=True)
                        col1, col2 = st.columns(2)
                        with col1:
                            grouped = filtered_df.groupby(['Booking Date', 'ADR']).size().reset_index(name='counts')
                            fig = px.bar(grouped, x='Booking Date', y='counts', color='ADR',color_discrete_map=color_scale, barmode='stack')
                            st.plotly_chart(fig,use_container_width=True)
                        with col2:
                            grouped = filtered_df.groupby(['Booking Date', 'Booking Source']).size().reset_index(name='counts')
                            fig = px.bar(grouped, x='Booking Date', y='counts', color='Booking Source',color_discrete_map=color_scale, barmode='stack')
                            st.plotly_chart(fig,use_container_width=True)

                    with t2:
                        col1, col2 = st.columns(2)
                        col1.markdown('Average Lead Time by booked and Room Type')
                        adr_avg = filtered_df.groupby(['Booking Date', 'Room type'])['Lead Time'].mean().reset_index()
                        fig = px.bar(adr_avg, x='Booking Date', y='Lead Time', color='Room type',text_auto=True)
                        fig.update_layout(legend=dict(orientation="h",yanchor="bottom",y=1.02,xanchor="right",x=1))
                        col1.plotly_chart(fig, use_container_width=True)
                        col2.markdown('Average Lead Time by booked')
                        adr_avg = filtered_df.groupby(['Booking Date'])['Lead Time'].mean().reset_index()
                        fig = px.bar(adr_avg, x='Booking Date', y='Lead Time',text_auto=True)
                        col2.plotly_chart(fig, use_container_width=True)
                        col1, col2 = st.columns(2)
                        with col1:
                            grouped = filtered_df.groupby(['Booking Date', 'Lead time range']).size().reset_index(name='counts')
                            fig = px.bar(grouped, x='Booking Date', y='counts', color='Lead time range',color_discrete_map=color_scale, barmode='stack')
                            st.plotly_chart(fig,use_container_width=True)
                        with col2:
                            grouped = filtered_df.groupby(['Booking Date', 'Booking Source']).size().reset_index(name='counts')
                            fig = px.bar(grouped, x='Booking Date', y='counts', color='Booking Source',color_discrete_map=color_scale, barmode='stack')
                            st.plotly_chart(fig,use_container_width=True)
                    with t3:
                        col1, col2 = st.columns(2)
                        col1.markdown('Average LOS by booked and Room Type')
                        adr_avg = filtered_df.groupby(['Booking Date', 'Room type'])['LOS'].mean().reset_index()
                        fig = px.bar(adr_avg, x='Booking Date', y='LOS', color='Room type',text_auto=True)
                        fig.update_layout(legend=dict(orientation="h",yanchor="bottom",y=1.02,xanchor="right",x=1))
                        col1.plotly_chart(fig, use_container_width=True)
                        col2.markdown('Average LOS by booked')
                        adr_avg = filtered_df.groupby(['Booking Date'])['LOS'].mean().reset_index()
                        fig = px.bar(adr_avg, x='Booking Date', y='LOS',text_auto=True)
                        col2.plotly_chart(fig, use_container_width=True)
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            grouped = filtered_df.groupby(['Booking Date', 'LOS']).size().reset_index(name='counts')
                            fig = px.bar(grouped, x='Booking Date', y='counts', color='LOS',color_discrete_map=color_scale, barmode='stack')
                            st.plotly_chart(fig,use_container_width=True)
                        with col2:
                            grouped = filtered_df.groupby(['Booking Date', 'Booking Source']).size().reset_index(name='counts')
                            fig = px.bar(grouped, x='Booking Date', y='counts', color='Booking Source',color_discrete_map=color_scale, barmode='stack')
                            st.plotly_chart(fig,use_container_width=True)
                    with t4:
                        col1, col2 = st.columns(2)
                        col1.markdown('Average RN by booked and Room Type')
                        adr_avg = filtered_df.groupby(['Booking Date', 'Room type'])['RN'].mean().reset_index()
                        fig = px.bar(adr_avg, x='Booking Date', y='RN', color='Room type',text_auto=True)
                        fig.update_layout(legend=dict(orientation="h",yanchor="bottom",y=1.02,xanchor="right",x=1))
                        col1.plotly_chart(fig, use_container_width=True)
                        col2.markdown('Average RN by booked')
                        adr_avg = filtered_df.groupby(['Booking Date'])['RN'].mean().reset_index()
                        fig = px.bar(adr_avg, x='Booking Date', y='RN',text_auto=True)
                        col2.plotly_chart(fig, use_container_width=True)
                        col1, col2 = st.columns(2)
                        with col1:
                            grouped = filtered_df.groupby(['Booking Date', 'RN']).size().reset_index(name='counts')
                            fig = px.bar(grouped, x='Booking Date', y='counts', color='RN',color_discrete_map=color_scale, barmode='stack')
                            st.plotly_chart(fig,use_container_width=True)
                        with col2:
                            grouped = filtered_df.groupby(['Booking Date', 'Booking Source']).size().reset_index(name='counts')
                            fig = px.bar(grouped, x='Booking Date', y='counts', color='Booking Source',color_discrete_map=color_scale, barmode='stack')
                            st.plotly_chart(fig,use_container_width=True)
                with tLT:
                    st.markdown('**Pivot table by lead time**')
                    t1,t2,t3 = st.tabs(['ADR','LOS','RN'])
                    with t1:
                        col1, col2 = st.columns(2)
                        col1.markdown('Average ADR by LT and Room Type')
                        adr_avg = filtered_df.groupby(['Lead time range', 'Room type'])['ADR'].mean().reset_index()
                        fig = px.bar(adr_avg, x='Lead time range', y='ADR', color='Room type',text_auto=True)
                        fig.update_layout(legend=dict(orientation="h",yanchor="bottom",y=1.02,xanchor="right",x=1))
                        col1.plotly_chart(fig, use_container_width=True)
                        col2.markdown('Average ADR by LT')
                        adr_avg = filtered_df.groupby(['Lead time range'])['ADR'].mean().reset_index()
                        fig = px.bar(adr_avg, x='Lead time range', y='ADR',text_auto=True)
                        col2.plotly_chart(fig, use_container_width=True)
                        col1, col2 = st.columns(2)
                        with col1:
                            grouped = filtered_df.groupby(['Lead time range', 'ADR']).size().reset_index(name='counts')
                            fig = px.bar(grouped, x='Lead time range', y='counts', color='ADR',color_discrete_map=color_scale, barmode='stack')
                            st.plotly_chart(fig)
                        with col2:
                            grouped = filtered_df.groupby(['Lead time range', 'Booking Source']).size().reset_index(name='counts')
                            fig = px.bar(grouped, x='Lead time range', y='counts', color='Booking Source',color_discrete_map=color_scale, barmode='stack')
                            st.plotly_chart(fig)
                    with t2:
                        col1, col2 = st.columns(2)
                        col1.markdown('Average LOS by LT and Room Type')
                        adr_avg = filtered_df.groupby(['Lead time range', 'Room type'])['LOS'].mean().reset_index()
                        fig = px.bar(adr_avg, x='Lead time range', y='LOS', color='Room type',text_auto=True)
                        fig.update_layout(legend=dict(orientation="h",yanchor="bottom",y=1.02,xanchor="right",x=1))
                        col1.plotly_chart(fig, use_container_width=True)
                        col2.markdown('Average LOS by LT')
                        adr_avg = filtered_df.groupby(['Lead time range'])['LOS'].mean().reset_index()
                        fig = px.bar(adr_avg, x='Lead time range', y='LOS',text_auto=True)
                        col2.plotly_chart(fig, use_container_width=True)
                        col1, col2 = st.columns(2)
                        with col1:
                            grouped = filtered_df.groupby(['Lead time range', 'LOS']).size().reset_index(name='counts')
                            fig = px.bar(grouped, x='Lead time range', y='counts', color='LOS',color_discrete_map=color_scale, barmode='stack')
                            st.plotly_chart(fig)
                        with col2:
                            grouped = filtered_df.groupby(['Lead time range', 'Booking Source']).size().reset_index(name='counts')
                            fig = px.bar(grouped, x='Lead time range', y='counts', color='Booking Source',color_discrete_map=color_scale, barmode='stack')
                            st.plotly_chart(fig)
                    with t3:
                        col1, col2 = st.columns(2)
                        col1.markdown('Average RN by LT and Room Type')
                        adr_avg = filtered_df.groupby(['Lead time range', 'Room type'])['RN'].mean().reset_index()
                        fig = px.bar(adr_avg, x='Lead time range', y='RN', color='Room type',text_auto=True)
                        fig.update_layout(legend=dict(orientation="h",yanchor="bottom",y=1.02,xanchor="right",x=1))
                        col1.plotly_chart(fig, use_container_width=True)
                        col2.markdown('Average RN by LT')
                        adr_avg = filtered_df.groupby(['Lead time range'])['RN'].mean().reset_index()
                        fig = px.bar(adr_avg, x='Lead time range', y='RN',text_auto=True)
                        col2.plotly_chart(fig, use_container_width=True)
                        col1, col2 = st.columns(2)
                        with col1:
                            grouped = filtered_df.groupby(['Lead time range', 'RN']).size().reset_index(name='counts')
                            fig = px.bar(grouped, x='Lead time range', y='counts', color='RN',color_discrete_map=color_scale, barmode='stack')
                            st.plotly_chart(fig)
                        with col2:
                            grouped = filtered_df.groupby(['Lead time range', 'Booking Source']).size().reset_index(name='counts')
                            fig = px.bar(grouped, x='Lead time range', y='counts', color='Booking Source',color_discrete_map=color_scale, barmode='stack')
                            st.plotly_chart(fig)
                with tLOS:
                    st.markdown('**Pivot table by LOS**')
                    t1,t2,t3 = st.tabs(['ADR','LT','RN'])
                    with t1:
                        col1, col2 = st.columns(2)
                        col1.markdown('Average ADR by LOS and Room Type')
                        adr_avg = filtered_df.groupby(['LOS', 'Room type'])['ADR'].mean().reset_index()
                        fig = px.bar(adr_avg, x='LOS', y='ADR', color='Room type',text_auto=True)
                        fig.update_layout(legend=dict(orientation="h",yanchor="bottom",y=1.02,xanchor="right",x=1))
                        col1.plotly_chart(fig, use_container_width=True)
                        col2.markdown('Average ADR by LOS')
                        adr_avg = filtered_df.groupby(['LOS'])['ADR'].mean().reset_index()
                        fig = px.bar(adr_avg, x='LOS', y='ADR',text_auto=True)
                        col2.plotly_chart(fig, use_container_width=True)
                        col1, col2 = st.columns(2)
                        with col1:
                            grouped = filtered_df.groupby(['LOS', 'ADR']).size().reset_index(name='counts')
                            fig = px.bar(grouped, x='LOS', y='counts', color='ADR',color_discrete_map=color_scale, barmode='stack')
                            st.plotly_chart(fig)
                        with col2:
                            grouped = filtered_df.groupby(['LOS', 'Booking Source']).size().reset_index(name='counts')
                            fig = px.bar(grouped, x='LOS', y='counts', color='Booking Source',color_discrete_map=color_scale, barmode='stack')
                            st.plotly_chart(fig)
                    with t2:
                        col1, col2 = st.columns(2)
                        col1.markdown('Average LT by LOS and Room Type')
                        adr_avg = filtered_df.groupby(['LOS', 'Room type'])['Lead Time'].mean().reset_index()
                        fig = px.bar(adr_avg, x='LOS', y='Lead Time', color='Room type',text_auto=True)
                        fig.update_layout(legend=dict(orientation="h",yanchor="bottom",y=1.02,xanchor="right",x=1))
                        col1.plotly_chart(fig, use_container_width=True)
                        col2.markdown('Average LT by LOS')
                        adr_avg = filtered_df.groupby(['LOS'])['Lead Time'].mean().reset_index()
                        fig = px.bar(adr_avg, x='LOS', y='Lead Time',text_auto=True)
                        col2.plotly_chart(fig, use_container_width=True)

                        col1, col2 = st.columns(2)
                        with col1:
                            grouped = filtered_df.groupby(['LOS', 'Lead Time']).size().reset_index(name='counts')
                            fig = px.bar(grouped, x='LOS', y='counts', color='Lead Time',color_discrete_map=color_scale, barmode='stack')
                            st.plotly_chart(fig)
                        with col2:
                            grouped = filtered_df.groupby(['LOS', 'Booking Source']).size().reset_index(name='counts')
                            fig = px.bar(grouped, x='LOS', y='counts', color='Booking Source',color_discrete_map=color_scale, barmode='stack')
                            st.plotly_chart(fig)
                    with t3:
                        col1, col2 = st.columns(2)
                        col1.markdown('Average RN by LOS and Room Type')
                        adr_avg = filtered_df.groupby(['LOS', 'Room type'])['RN'].mean().reset_index()
                        fig = px.bar(adr_avg, x='LOS', y='RN', color='Room type',text_auto=True)
                        fig.update_layout(legend=dict(orientation="h",yanchor="bottom",y=1.02,xanchor="right",x=1))
                        col1.plotly_chart(fig, use_container_width=True)
                        col2.markdown('Average RN by LOS')
                        adr_avg = filtered_df.groupby(['LOS'])['RN'].mean().reset_index()
                        fig = px.bar(adr_avg, x='LOS', y='RN',text_auto=True)
                        col2.plotly_chart(fig, use_container_width=True)
                        col1, col2 = st.columns(2)
                        with col1:
                            grouped = filtered_df.groupby(['LOS', 'RN']).size().reset_index(name='counts')
                            fig = px.bar(grouped, x='LOS', y='counts', color='RN',color_discrete_map=color_scale, barmode='stack')
                            st.plotly_chart(fig)
                        with col2:
                            grouped = filtered_df.groupby(['LOS', 'Booking Source']).size().reset_index(name='counts')
                            fig = px.bar(grouped, x='LOS', y='counts', color='Booking Source',color_discrete_map=color_scale, barmode='stack')
                            st.plotly_chart(fig)


            with tab_stay:
                all3 =  perform(all2)
                if selected_channels:
                    filtered_df = all3[all3['Booking Source'].isin(selected_channels)]
                    if selected_room_types:
                        if 'All' not in selected_room_types:
                            filtered_df = filtered_df[filtered_df['Room type'].isin(selected_room_types)]
                    else:
                        if selected_room_types:
                            if 'All' not in selected_room_types:
                                filtered_df = all3[all3['Room type'].isin(selected_room_types)]
                else:
                    filtered_df = all3

                filtered_df['Stay'] = filtered_df.apply(lambda row: pd.date_range(row['Check-in'], row['Check-out']- pd.Timedelta(days=1)), axis=1)
                filtered_df = filtered_df.explode('Stay').reset_index(drop=True)
                filtered_df = filtered_df[['Stay','Check-in','Check-out','Booking Source','ADR','LOS','Lead Time','Lead time range','RN','Quantity','Room type']]

                filtered_df['Day Name'] = filtered_df['Stay'].dt.strftime('%A')
                filtered_df['Week of Year'] = filtered_df['Stay'].dt.isocalendar().week
                filtered_df = filtered_df.dropna()

                month_dict = {v: k for k, v in enumerate(calendar.month_name)}
                months = list(calendar.month_name)[1:]
                selected_month = st.multiselect('Select a month stay', months)

                # Assuming you have a select year input stored in the variable 'selected_year'
                selected_year = st.selectbox('Select a year', ['2022', '2023', '2024','2025','2026'], index=1)

                if selected_month and selected_year:
                    selected_month_nums = [month_dict[month_name] for month_name in selected_month]
                    filtered_df = filtered_df[
                        (filtered_df['Stay'].dt.month.isin(selected_month_nums)) &
                        (filtered_df['Stay'].dt.year == int(selected_year))
                    ]
                elif selected_month:
                    selected_month_nums = [month_dict[month_name] for month_name in selected_month]
                    filtered_df = filtered_df[filtered_df['Stay'].dt.month.isin(selected_month_nums)]
                elif selected_year:
                    filtered_df = filtered_df[filtered_df['Stay'].dt.year == int(selected_year)]
                    

                col1 , col2 = st.columns(2)
                with col2:
                    filter_LT = st.checkbox('Filter by LT')
                    if filter_LT:
                        min_val, max_val = int(filtered_df['Lead Time'].min()), int(filtered_df['Lead Time'].max())
                        LT_min, LT_max = st.slider('Select a range of LT', min_val, max_val, (min_val, max_val))
                        filtered_df = filtered_df[(filtered_df['Lead Time'] >= LT_min) & (filtered_df['Lead Time'] <= LT_max)]
                    else:
                        filtered_df = filtered_df.copy()
                with col1:
                    filter_LOS = st.checkbox('Filter by LOS')
                    if filter_LOS:
                        min_val, max_val = int(filtered_df['LOS'].min()), int(filtered_df['LOS'].max())
                        LOS_min, LOS_max = st.slider('Select a range of LOS', min_val, max_val, (min_val, max_val))
                        filtered_df = filtered_df[(filtered_df['LOS'] >= LOS_min) & (filtered_df['LOS'] <= LOS_max)]
                    else:
                        filtered_df = filtered_df.copy()
                
                tab1, tab2, tab3 ,tab4, tab5 , tab6 ,tab7= st.tabs(["Average", "Median", "Statistic",'Data'
                                                                    ,'Bar Chart','Room roomnight by channel'
                                                                    ,'Room revenue by channel'])
                with tab1:
                    col0,col00, col1, col2, col4 = st.columns(5)
                    filtered_df['ADR discount'] = filtered_df["ADR"]*filtered_df["LOS"]*filtered_df["Quantity"]
                    min_s = filtered_df["Stay"].min()
                    max_s = filtered_df["Stay"].max()
                    per_period = (max_s - min_s).days
                    col00.metric('**Revenue per number of period(Stay)**',f'{round((filtered_df["ADR discount"].sum()/per_period),1)}')
                    col0.metric('**Revenue**',f'{round(filtered_df["ADR discount"].sum(),0)}')
                    col4.metric('**ADR with discount commission and ABF**',f'{round(filtered_df["ADR"].mean(),1)}',)
                    col1.metric("**A.LT**", f'{round(filtered_df["Lead Time"].mean(),1)}')
                    col2.metric("**A.LOS**", f'{round(filtered_df["LOS"].mean(),1)}')
                with tab2:
                    col1, col2, col3 = st.columns(3)
                    col3.metric('ADR with discount commission',f'{round(filtered_df["ADR"].median(),1)}')
                    col1.metric("A.LT", f'{round(filtered_df["Lead Time"].median(),1)}')
                    col2.metric("A.LOS", f'{round(filtered_df["LOS"].median(),1)}')
                with tab3:
                    st.write(filtered_df.describe())
                with tab4:
                    st.write(filtered_df)
                with tab5:
                    tab11, tab12, tab13, tab14 = st.tabs(['A.LT','A.LOS','A.RN','ADR by month'])
                    with tab14:
                        month_order = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
                        mean_adr_by_month = filtered_df.groupby(['Room type', filtered_df['Stay'].dt.month_name()])['ADR'].mean().reset_index()
                        mean_adr_by_month['Stay'] = pd.Categorical(mean_adr_by_month['Stay'], categories=month_order)

                        bar_chart = px.bar(mean_adr_by_month, x='Stay', y='ADR', color='Room type',category_orders={'Stay': month_order},
                                    text='ADR')
                        bar_chart.update_traces(texttemplate='%{text:.2f}', textposition='auto')
                        st.plotly_chart(bar_chart, use_container_width=True)
                    with tab11:
                        month_order = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
                        mean_adr_by_month = filtered_df.groupby(['Room type', filtered_df['Stay'].dt.month_name()])['Lead Time'].mean().reset_index()
                        mean_adr_by_month['Stay'] = pd.Categorical(mean_adr_by_month['Stay'], categories=month_order)

                        bar_chart = px.bar(mean_adr_by_month, x='Stay', y='Lead Time', color='Room type',category_orders={'Stay': month_order},
                                    text='Lead Time')
                        bar_chart.update_traces(texttemplate='%{text:.2f}', textposition='auto')
                        st.plotly_chart(bar_chart, use_container_width=True)
                    with tab12:
                        month_order = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
                        mean_adr_by_month = filtered_df.groupby(['Room type', filtered_df['Stay'].dt.month_name()])['LOS'].mean().reset_index()
                        mean_adr_by_month['Stay'] = pd.Categorical(mean_adr_by_month['Stay'], categories=month_order)

                        bar_chart = px.bar(mean_adr_by_month, x='Stay', y='LOS', color='Room type',category_orders={'Stay': month_order},
                                text='LOS')
                        bar_chart.update_traces(texttemplate='%{text:.2f}', textposition='auto')
                        st.plotly_chart(bar_chart, use_container_width=True)
                    with tab13:
                        month_order = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
                        mean_adr_by_month = filtered_df.groupby(['Room type', filtered_df['Stay'].dt.month_name()])['RN'].mean().reset_index()
                        mean_adr_by_month['Stay'] = pd.Categorical(mean_adr_by_month['Stay'], categories=month_order)

                        bar_chart = px.bar(mean_adr_by_month, x='Stay', y='RN', color='Room type',category_orders={'Stay': month_order},
                                    text='RN')
                        bar_chart.update_traces(texttemplate='%{text:.2f}', textposition='auto')
                        st.plotly_chart(bar_chart, use_container_width=True)
                with tab6:
                    counts = filtered_df[['Booking Source', 'Room type','RN']].groupby(['Booking Source', 'Room type']).sum().reset_index()
                    fig = px.treemap(counts, path=['Booking Source', 'Room type','RN'], values='RN', color='RN',color_continuous_scale='YlOrRd')
                    st.plotly_chart(fig, use_container_width=True)
                with tab7:
                    counts = filtered_df[['Booking Source', 'Room type','ADR discount']].groupby(['Booking Source', 'Room type']).sum().reset_index()
                    fig = px.treemap(counts, path=['Booking Source', 'Room type','ADR discount'], values='ADR discount', color='ADR discount',color_continuous_scale='YlOrRd')
                    st.plotly_chart(fig, use_container_width=True)
                    
                ADR_S,LOS_S,LT_S = st.tabs(['**ADR by Booking Source and room type**','**LOS by Booking Source and room type**','**LT by Booking Source and room type**'])
                with ADR_S:
                    st.markdown('**avg ADR without comm and ABF by Channel and room type (if you do not filter month, it would be all month)**')
                    df_january = filtered_df[['Stay','Booking Source','Room type','ADR']]
                    avg_adr = df_january.groupby(['Booking Source', 'Room type'])['ADR'].mean()
                    result = avg_adr.reset_index().pivot_table(values='ADR', index='Booking Source', columns='Room type', fill_value='none')
                    avg_adr_all_room_type = df_january.groupby(['Booking Source'])['ADR'].mean()
                    result['ALL ROOM TYPE'] = avg_adr_all_room_type
                    result = result.applymap(lambda x: int(x)  if x != 'none' else 'none')
                    st.write(result,use_container_width=True)
                with LOS_S:
                    st.markdown('**avg LOS without comm and ABF by Channel and room type (if you do not filter month, it would be all month)**')
                    df_january = filtered_df[['Stay','Booking Source','Room type','LOS']]
                    avg_adr = df_january.groupby(['Booking Source', 'Room type'])['LOS'].mean()
                    result = avg_adr.reset_index().pivot_table(values='LOS', index='Booking Source', columns='Room type', fill_value='none')
                    avg_adr_all_room_type = df_january.groupby(['Booking Source'])['LOS'].mean()
                    result['ALL ROOM TYPE'] = avg_adr_all_room_type
                    result = result.applymap(lambda x: int(x)  if x != 'none' else 'none')
                    st.write(result,use_container_width=True)
                with LT_S:
                    st.markdown('**avg LT without comm and ABF by Channel and room type (if you do not filter month, it would be all month)**')
                    df_january = filtered_df[['Stay','Booking Source','Room type','Lead Time']]
                    avg_adr = df_january.groupby(['Booking Source', 'Room type'])['Lead Time'].mean()
                    result = avg_adr.reset_index().pivot_table(values='Lead Time', index='Booking Source', columns='Room type', fill_value='none')
                    avg_adr_all_room_type = df_january.groupby(['Booking Source'])['Lead Time'].mean()
                    result['ALL ROOM TYPE'] = avg_adr_all_room_type
                    result = result.applymap(lambda x: int(x)  if x != 'none' else 'none')
                    st.write(result,use_container_width=True)


                st.markdown('**You can zoom in**')
                col1, col2 = st.columns(2)
                channels = filtered_df['Booking Source'].unique()
                num_colors = len(channels)
                colors = px.colors.qualitative.Plotly
                color_scale =  {channel: colors[i % num_colors] for i, channel in enumerate(channels)}
                with col1:
                    grouped = filtered_df.groupby(['Stay', 'Booking Source']).size().reset_index(name='counts')
                    fig = px.bar(grouped, x='Stay', y='counts', color='Booking Source',color_discrete_map=color_scale, barmode='stack')
                    st.plotly_chart(fig)
                with col2:
                    grouped = filtered_df.groupby(['Lead time range', 'Booking Source']).size().reset_index(name='counts')
                    fig = px.bar(grouped, x='Lead time range', y='counts', color='Booking Source',color_discrete_map=color_scale, barmode='stack')
                    st.plotly_chart(fig)

                col1, col2 = st.columns(2)
                with col1:
                    st.markdown('**count Stay in week of Year (calendar)**')
                    pt = filtered_df.pivot_table(index='Week of Year', columns='Day Name', aggfunc='size')
                    if set(['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']).issubset(filtered_df['Day Name'].unique()):
                        pt = filtered_df.pivot_table(index='Week of Year', columns='Day Name', aggfunc='size', fill_value=0)
                        pt = pt[['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']]
                        st.write(pt.style.background_gradient(cmap='coolwarm', axis=1))
                    else:
                        st.write('Not enough data to create a pivot table')
                with col2:
                    st.markdown('**A.LT that Check-in in week of Year (calendar)**')
                    grouped = filtered_df.groupby(['Week of Year', 'Day Name'])
                    averages = grouped['Lead Time'].mean().reset_index()
                    pt = pd.pivot_table(averages, values='Lead Time', index=['Week of Year'], columns=['Day Name'])
                    if set(['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']).issubset(filtered_df['Day Name'].unique()):
                        pt = pt.loc[:, ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']]
                        st.write(pt.style.format("{:.2f}").background_gradient(cmap='coolwarm', axis=1))
                    else:
                        st.write('Not enough data to create a pivot table')

                st.markdown('**Pivot table by Stay**')
                t1,t2,t3,t4 = st.tabs(['ADR','LT','LOS','RN'])
                with t1:
                    col1, col2 = st.columns(2)
                    #filtered_df_pi = pd.pivot_table(filtered_df, index='Booked',values=['ADR'])
                    col1.markdown('Average ADR by Stay and Room Type')
                    #st.bar_chart(filtered_df_pi)
                    adr_avg = filtered_df.groupby(['Stay', 'Room type'])['ADR'].mean().reset_index()
                    fig = px.bar(adr_avg, x='Stay', y='ADR', color='Room type',text_auto=True)
                    fig.update_layout(legend=dict(orientation="h",yanchor="bottom",y=1.02,xanchor="right",x=1))
                    col1.plotly_chart(fig, use_container_width=True)
                    #filtered_df_pi = pd.pivot_table(filtered_df, index='Booked',values=['ADR'])
                    col2.markdown('Average ADR by Stay')
                    #st.bar_chart(filtered_df_pi)
                    adr_avg = filtered_df.groupby(['Stay'])['ADR'].mean().reset_index()
                    fig = px.bar(adr_avg, x='Stay', y='ADR',text_auto=True)
                    col2.plotly_chart(fig, use_container_width=True)
                    col1, col2 = st.columns(2)
                    with col1:
                        grouped = filtered_df.groupby(['Stay', 'ADR']).size().reset_index(name='counts')
                        fig = px.bar(grouped, x='Stay', y='counts', color='ADR',color_discrete_map=color_scale, barmode='stack')
                        st.plotly_chart(fig,use_container_width=True)
                    with col2:
                        grouped = filtered_df.groupby(['Stay', 'Booking Source']).size().reset_index(name='counts')
                        fig = px.bar(grouped, x='Stay', y='counts', color='Booking Source',color_discrete_map=color_scale, barmode='stack')
                        st.plotly_chart(fig,use_container_width=True)

                with t2:
                    col1, col2 = st.columns(2)
                    col1.markdown('Average Lead Time by Stay and Room Type')
                    adr_avg = filtered_df.groupby(['Stay', 'Room type'])['Lead Time'].mean().reset_index()
                    fig = px.bar(adr_avg, x='Stay', y='Lead Time', color='Room type',text_auto=True)
                    fig.update_layout(legend=dict(orientation="h",yanchor="bottom",y=1.02,xanchor="right",x=1))
                    col1.plotly_chart(fig, use_container_width=True)
                    col2.markdown('Average Lead Time by Stay')
                    adr_avg = filtered_df.groupby(['Stay'])['Lead Time'].mean().reset_index()
                    fig = px.bar(adr_avg, x='Stay', y='Lead Time',text_auto=True)
                    col2.plotly_chart(fig, use_container_width=True)
                    col1, col2 = st.columns(2)
                    with col1:
                        grouped = filtered_df.groupby(['Stay', 'Lead time range']).size().reset_index(name='counts')
                        fig = px.bar(grouped, x='Stay', y='counts', color='Lead time range',color_discrete_map=color_scale, barmode='stack')
                        st.plotly_chart(fig,use_container_width=True)
                    with col2:
                        grouped = filtered_df.groupby(['Stay', 'Booking Source']).size().reset_index(name='counts')
                        fig = px.bar(grouped, x='Stay', y='counts', color='Booking Source',color_discrete_map=color_scale, barmode='stack')
                        st.plotly_chart(fig,use_container_width=True)
                with t3:
                    col1, col2 = st.columns(2)
                    col1.markdown('Average LOS by Stay and Room Type')
                    adr_avg = filtered_df.groupby(['Stay', 'Room type'])['LOS'].mean().reset_index()
                    fig = px.bar(adr_avg, x='Stay', y='LOS', color='Room type',text_auto=True)
                    fig.update_layout(legend=dict(orientation="h",yanchor="bottom",y=1.02,xanchor="right",x=1))
                    col1.plotly_chart(fig, use_container_width=True)
                    col2.markdown('Average LOS by Stay')
                    adr_avg = filtered_df.groupby(['Stay'])['LOS'].mean().reset_index()
                    fig = px.bar(adr_avg, x='Stay', y='LOS',text_auto=True)
                    col2.plotly_chart(fig, use_container_width=True)
                        
                    col1, col2 = st.columns(2)
                    with col1:
                        grouped = filtered_df.groupby(['Stay', 'LOS']).size().reset_index(name='counts')
                        fig = px.bar(grouped, x='Stay', y='counts', color='LOS',color_discrete_map=color_scale, barmode='stack')
                        st.plotly_chart(fig,use_container_width=True)
                    with col2:
                        grouped = filtered_df.groupby(['Stay', 'Booking Source']).size().reset_index(name='counts')
                        fig = px.bar(grouped, x='Stay', y='counts', color='Booking Source',color_discrete_map=color_scale, barmode='stack')
                        st.plotly_chart(fig,use_container_width=True)
                with t4:
                    col1, col2 = st.columns(2)
                    col1.markdown('Average RN by Stay and Room Type')
                    adr_avg = filtered_df.groupby(['Stay', 'Room type'])['RN'].mean().reset_index()
                    fig = px.bar(adr_avg, x='Stay', y='RN', color='Room type',text_auto=True)
                    fig.update_layout(legend=dict(orientation="h",yanchor="bottom",y=1.02,xanchor="right",x=1))
                    col1.plotly_chart(fig, use_container_width=True)
                    col2.markdown('Average RN by Stay')
                    adr_avg = filtered_df.groupby(['Stay'])['RN'].mean().reset_index()
                    fig = px.bar(adr_avg, x='Stay', y='RN',text_auto=True)
                    col2.plotly_chart(fig, use_container_width=True)
                    col1, col2 = st.columns(2)
                    with col1:
                        grouped = filtered_df.groupby(['Stay', 'RN']).size().reset_index(name='counts')
                        fig = px.bar(grouped, x='Stay', y='counts', color='RN',color_discrete_map=color_scale, barmode='stack')
                        st.plotly_chart(fig,use_container_width=True)
                    with col2:
                        grouped = filtered_df.groupby(['Stay', 'Booking Source']).size().reset_index(name='counts')
                        fig = px.bar(grouped, x='Stay', y='counts', color='Booking Source',color_discrete_map=color_scale, barmode='stack')
                        st.plotly_chart(fig,use_container_width=True)

else:
    st.markdown("**No file uploaded.**")
    st.markdown('Upload the file from the **travelanium**, then select the Reservations and select the data type **Booked-on** or **Check-in**')
    st.markdown('**GUIDE**')
    st.markdown('-You can multiselect Channels. If you do not select anything, It would be All Channels')
    st.markdown('-You can multiselect Room Type. If you do not select anything, It would be All Room Type')
    st.markdown('**-NOTE**: Rev and ADR discount **Commission** and **ABF**')
    st.markdown('')
