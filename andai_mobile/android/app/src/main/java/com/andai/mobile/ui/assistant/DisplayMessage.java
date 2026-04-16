package com.andai.mobile.ui.assistant;

import com.google.gson.JsonObject;

public class DisplayMessage {
    public String role;
    public String content;
    public JsonObject sources;
    public String modelTier;
    public Integer responseTimeMs;
    public String createdAt;

    public DisplayMessage(String role, String content) {
        this.role = role;
        this.content = content;
    }
}
