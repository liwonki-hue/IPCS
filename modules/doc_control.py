# [위의 기존 코드와 동일하며 show_doc_control 함수의 st.dataframe 부분만 아래와 같이 업데이트합니다]

    # 5. Data Viewport (Optimized Column Widths)
    display_cols = ["Category", "SYSTEM", "DWG. NO.", "Description", "Rev", "Date", "Hold", "Status", "Remark"]
    
    st.dataframe(
        f_df[display_cols], 
        use_container_width=True, 
        hide_index=True, 
        height=750,
        column_config={
            # Narrow columns to save space
            "Category": st.column_config.TextColumn("Category", width="small"),
            "SYSTEM": st.column_config.TextColumn("SYSTEM", width="small"),
            "Rev": st.column_config.TextColumn("Rev", width="small"),
            "Date": st.column_config.TextColumn("Date", width="small"),
            "Hold": st.column_config.TextColumn("Hold", width="small"),
            "Status": st.column_config.TextColumn("Status", width="small"),
            
            # Expanded columns for full visibility
            "DWG. NO.": st.column_config.TextColumn("DWG. NO.", width="medium"),
            "Description": st.column_config.TextColumn(
                "Description", 
                width="large",      # Allocate maximum width
                help="Full Drawing Title"
            ),
            "Remark": st.column_config.TextColumn(
                "Remark", 
                width="medium"      # Adjusted to balance with Description
            )
        }
    )
