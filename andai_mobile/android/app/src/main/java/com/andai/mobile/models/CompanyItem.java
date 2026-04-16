package com.andai.mobile.models;

import com.google.gson.annotations.SerializedName;

public class CompanyItem {
    public int id;
    public String name;
    public String slug;
    public String description;
    @SerializedName("is_active")
    public boolean isActive;
    @SerializedName("created_at")
    public String createdAt;
    @SerializedName("updated_at")
    public String updatedAt;
}
