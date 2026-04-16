package com.andai.mobile.models;

import com.google.gson.annotations.SerializedName;

public class AdminUser {
    public int id;
    public String email;
    @SerializedName("full_name")
    public String fullName;
    public String role;
    @SerializedName("company_id")
    public Integer companyId;
    @SerializedName("company_name")
    public String companyName;
    @SerializedName("is_active")
    public boolean isActive;
    @SerializedName("created_at")
    public String createdAt;
}
