package com.andai.mobile.models;

import com.google.gson.JsonObject;
import com.google.gson.annotations.SerializedName;

public class AuditLogItem {
    public int id;
    @SerializedName("company_id")
    public Integer companyId;
    @SerializedName("user_id")
    public Integer userId;
    public String action;
    @SerializedName("resource_type")
    public String resourceType;
    @SerializedName("resource_id")
    public Integer resourceId;
    public JsonObject details;
    @SerializedName("ip_address")
    public String ipAddress;
    @SerializedName("created_at")
    public String createdAt;
}
