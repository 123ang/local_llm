package com.andai.mobile.models;

import com.google.gson.annotations.SerializedName;

public class User {
    public int id;
    public String email;
    @SerializedName("full_name")
    public String fullName;
    public String role;
    @SerializedName("company_id")
    public Integer companyId;
    @SerializedName("company_name")
    public String companyName;

    public boolean isAdmin() {
        return "admin".equals(role) || "super_admin".equals(role);
    }

    public boolean isSuperAdmin() {
        return "super_admin".equals(role);
    }
}
