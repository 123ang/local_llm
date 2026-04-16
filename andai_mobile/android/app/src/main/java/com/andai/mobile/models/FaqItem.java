package com.andai.mobile.models;

import com.google.gson.annotations.SerializedName;

public class FaqItem {
    public int id;
    @SerializedName("company_id")
    public int companyId;
    public String question;
    public String answer;
    public String category;
    @SerializedName("is_published")
    public boolean isPublished;
    @SerializedName("sort_order")
    public int sortOrder;
    @SerializedName("created_at")
    public String createdAt;
    @SerializedName("updated_at")
    public String updatedAt;
}
