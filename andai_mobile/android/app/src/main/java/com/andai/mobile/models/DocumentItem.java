package com.andai.mobile.models;

import com.google.gson.annotations.SerializedName;

public class DocumentItem {
    public int id;
    @SerializedName("company_id")
    public int companyId;
    public String filename;
    @SerializedName("original_name")
    public String originalName;
    @SerializedName("file_size")
    public Integer fileSize;
    @SerializedName("mime_type")
    public String mimeType;
    public String status;
    @SerializedName("page_count")
    public Integer pageCount;
    @SerializedName("chunk_count")
    public int chunkCount;
    @SerializedName("error_message")
    public String errorMessage;
    @SerializedName("created_at")
    public String createdAt;
}
