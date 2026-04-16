package com.andai.mobile.models;

import com.google.gson.annotations.SerializedName;

public class ChatSession {
    public int id;
    public String title;
    @SerializedName("created_at")
    public String createdAt;
    @SerializedName("message_count")
    public int messageCount;
}
