package com.andai.mobile.models;

import com.google.gson.JsonObject;
import com.google.gson.annotations.SerializedName;

public class ChatMessage {
    public int id;
    public String role;
    public String content;
    public JsonObject sources;
    @SerializedName("created_at")
    public String createdAt;
    @SerializedName("model_tier")
    public String modelTier;
    @SerializedName("response_time_ms")
    public Integer responseTimeMs;
}
