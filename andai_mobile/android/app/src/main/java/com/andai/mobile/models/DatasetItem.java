package com.andai.mobile.models;

import com.google.gson.JsonArray;
import com.google.gson.annotations.SerializedName;

public class DatasetItem {
    public int id;
    @SerializedName("company_id")
    public int companyId;
    @SerializedName("table_name")
    public String tableName;
    @SerializedName("display_name")
    public String displayName;
    public String description;
    @SerializedName("columns_schema")
    public JsonArray columnsSchema;
    @SerializedName("row_count")
    public int rowCount;
    public String source;
    public String status;
    @SerializedName("is_queryable")
    public boolean isQueryable;
    @SerializedName("created_at")
    public String createdAt;
    @SerializedName("updated_at")
    public String updatedAt;

    public int getColumnCount() {
        return columnsSchema != null ? columnsSchema.size() : 0;
    }
}
