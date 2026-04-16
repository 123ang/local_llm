package com.andai.mobile.models;

import com.google.gson.JsonObject;
import com.google.gson.annotations.SerializedName;

public class ChatResponse {
    public String message;
    @SerializedName("session_id")
    public int sessionId;
    public JsonObject sources;
    @SerializedName("model_tier")
    public String modelTier;
    @SerializedName("response_time_ms")
    public Integer responseTimeMs;
}
