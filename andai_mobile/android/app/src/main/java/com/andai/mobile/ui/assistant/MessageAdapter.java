package com.andai.mobile.ui.assistant;

import android.content.Context;
import android.content.res.ColorStateList;
import android.graphics.Color;
import android.view.Gravity;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.LinearLayout;

import androidx.annotation.NonNull;
import androidx.core.content.ContextCompat;
import androidx.recyclerview.widget.RecyclerView;

import com.andai.mobile.R;
import com.andai.mobile.databinding.ItemMessageBinding;
import com.google.android.material.chip.Chip;
import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;

import java.util.ArrayList;
import java.util.List;

public class MessageAdapter extends RecyclerView.Adapter<MessageAdapter.VH> {

    private final List<DisplayMessage> items = new ArrayList<>();
    private final LayoutInflater inflater;

    public MessageAdapter(Context context) {
        this.inflater = LayoutInflater.from(context);
    }

    public void setItems(List<DisplayMessage> next) {
        items.clear();
        if (next != null) {
            items.addAll(next);
        }
        notifyDataSetChanged();
    }

    public void add(DisplayMessage m) {
        items.add(m);
        notifyItemInserted(items.size() - 1);
    }

    public void updateLastContent(String content) {
        if (items.isEmpty()) return;
        DisplayMessage last = items.get(items.size() - 1);
        last.content = content;
        notifyItemChanged(items.size() - 1);
    }

    @NonNull
    @Override
    public VH onCreateViewHolder(@NonNull ViewGroup parent, int viewType) {
        ItemMessageBinding b = ItemMessageBinding.inflate(inflater, parent, false);
        return new VH(b);
    }

    @Override
    public void onBindViewHolder(@NonNull VH holder, int position) {
        DisplayMessage m = items.get(position);
        ItemMessageBinding b = holder.binding;
        boolean user = "user".equals(m.role);

        b.tvContent.setText(m.content);

        LinearLayout.LayoutParams colLp =
                (LinearLayout.LayoutParams) b.columnBubble.getLayoutParams();
        LinearLayout.LayoutParams cardLp =
                (LinearLayout.LayoutParams) b.cardMessage.getLayoutParams();

        if (user) {
            b.ivBotAvatar.setVisibility(View.GONE);
            b.ivUserAvatar.setVisibility(View.VISIBLE);
            b.columnBubble.setGravity(Gravity.END);
            colLp.gravity = Gravity.END;
            cardLp.gravity = Gravity.END;
            b.cardMessage.setCardBackgroundColor(
                    b.getRoot().getContext().getColor(R.color.primary));
            b.tvContent.setTextColor(Color.WHITE);
        } else {
            b.ivBotAvatar.setVisibility(View.VISIBLE);
            b.ivUserAvatar.setVisibility(View.GONE);
            b.columnBubble.setGravity(Gravity.START);
            colLp.gravity = Gravity.START;
            cardLp.gravity = Gravity.START;
            b.cardMessage.setCardBackgroundColor(
                    b.getRoot().getContext().getColor(R.color.slate100));
            b.tvContent.setTextColor(
                    b.getRoot().getContext().getColor(R.color.text_primary));
        }
        b.columnBubble.setLayoutParams(colLp);
        b.cardMessage.setLayoutParams(cardLp);

        b.layoutSources.removeAllViews();
        if (!user && m.sources != null && m.sources.size() > 0) {
            b.layoutSources.setVisibility(View.VISIBLE);
            addSourceChips(b, m.sources);
        } else {
            b.layoutSources.setVisibility(View.GONE);
        }

        if (!user && (m.modelTier != null || m.responseTimeMs != null)) {
            b.tvMeta.setVisibility(View.VISIBLE);
            StringBuilder sb = new StringBuilder();
            if (m.modelTier != null) {
                sb.append(m.modelTier);
            }
            if (m.responseTimeMs != null) {
                if (sb.length() > 0) sb.append(" · ");
                sb.append(m.responseTimeMs).append(" ms");
            }
            if (m.createdAt != null && !m.createdAt.isEmpty()) {
                if (sb.length() > 0) sb.append(" · ");
                sb.append(m.createdAt.length() > 19 ? m.createdAt.substring(0, 19) : m.createdAt);
            }
            b.tvMeta.setText(sb.toString());
        } else {
            b.tvMeta.setVisibility(View.GONE);
        }
    }

    private void addSourceChips(ItemMessageBinding b, JsonObject sources) {
        Context ctx = b.getRoot().getContext();
        if (sources.has("faq") && sources.get("faq").isJsonArray()) {
            JsonArray faq = sources.getAsJsonArray("faq");
            if (faq.size() > 0) {
                Chip chip = new Chip(ctx);
                chip.setText(ctx.getString(R.string.source_faq) + ": " + faq.size());
                chip.setChipBackgroundColor(ColorStateList.valueOf(
                        ContextCompat.getColor(ctx, R.color.emerald50)));
                chip.setEnsureMinTouchTargetSize(false);
                b.layoutSources.addView(chip);
            }
        }
        if (sources.has("documents") && sources.get("documents").isJsonArray()) {
            JsonArray docs = sources.getAsJsonArray("documents");
            int max = Math.min(docs.size(), 4);
            for (int i = 0; i < max; i++) {
                JsonElement el = docs.get(i);
                String label = "Doc";
                if (el.isJsonObject()) {
                    JsonObject o = el.getAsJsonObject();
                    if (o.has("source") && !o.get("source").isJsonNull()) {
                        label = o.get("source").getAsString();
                    }
                }
                Chip chip = new Chip(ctx);
                chip.setText(label);
                chip.setChipBackgroundColor(ColorStateList.valueOf(
                        ContextCompat.getColor(ctx, R.color.blue50)));
                chip.setEnsureMinTouchTargetSize(false);
                b.layoutSources.addView(chip);
            }
            if (docs.size() > max) {
                Chip chip = new Chip(ctx);
                chip.setText("+" + (docs.size() - max));
                chip.setEnsureMinTouchTargetSize(false);
                b.layoutSources.addView(chip);
            }
        }
        if (sources.has("database") && sources.get("database").isJsonObject()) {
            JsonObject db = sources.getAsJsonObject("database");
            int rows = 0;
            if (db.has("row_count") && !db.get("row_count").isJsonNull()) {
                rows = db.get("row_count").getAsInt();
            }
            Chip chip = new Chip(ctx);
            chip.setText(ctx.getString(R.string.source_database) + ": " + rows + " rows");
            chip.setChipBackgroundColor(ColorStateList.valueOf(
                    ContextCompat.getColor(ctx, R.color.violet50)));
            chip.setEnsureMinTouchTargetSize(false);
            b.layoutSources.addView(chip);
        }
    }

    @Override
    public int getItemCount() {
        return items.size();
    }

    static class VH extends RecyclerView.ViewHolder {
        final ItemMessageBinding binding;

        VH(ItemMessageBinding binding) {
            super(binding.getRoot());
            this.binding = binding;
        }
    }
}
