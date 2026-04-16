package com.andai.mobile.ui.audit;

import android.os.Bundle;
import android.text.TextUtils;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.Toast;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.fragment.app.Fragment;
import androidx.recyclerview.widget.LinearLayoutManager;
import androidx.recyclerview.widget.RecyclerView;

import com.andai.mobile.R;
import com.andai.mobile.api.ApiClient;
import com.andai.mobile.databinding.FragmentAuditBinding;
import com.andai.mobile.databinding.ItemAuditBinding;
import com.andai.mobile.models.AuditLogItem;
import com.andai.mobile.utils.AuthManager;
import com.google.gson.Gson;
import com.google.gson.JsonSyntaxException;
import com.google.gson.reflect.TypeToken;

import java.lang.reflect.Type;
import java.util.ArrayList;
import java.util.List;

public class AuditFragment extends Fragment {

    private FragmentAuditBinding binding;
    private final Gson gson = new Gson();
    private final List<AuditLogItem> items = new ArrayList<>();
    private AuditAdapter adapter;

    @Nullable
    @Override
    public View onCreateView(@NonNull LayoutInflater inflater, @Nullable ViewGroup container,
                             @Nullable Bundle savedInstanceState) {
        binding = FragmentAuditBinding.inflate(inflater, container, false);
        return binding.getRoot();
    }

    @Override
    public void onViewCreated(@NonNull View view, @Nullable Bundle savedInstanceState) {
        super.onViewCreated(view, savedInstanceState);
        adapter = new AuditAdapter();
        binding.rvAudit.setLayoutManager(new LinearLayoutManager(requireContext()));
        binding.rvAudit.setAdapter(adapter);
        loadAudit();
    }

    private void loadAudit() {
        AuthManager auth = AuthManager.getInstance(requireContext());
        Integer companyId = auth.isSuperAdmin() ? null : auth.getCompanyId();

        binding.progress.setVisibility(View.VISIBLE);
        ApiClient.getInstance().getAuditLogs(companyId, 200, 0, new ApiClient.ApiCallback() {
            @Override
            public void onSuccess(String responseBody) {
                if (!isAdded()) return;
                binding.progress.setVisibility(View.GONE);
                try {
                    Type type = new TypeToken<List<AuditLogItem>>() {
                    }.getType();
                    List<AuditLogItem> list = gson.fromJson(responseBody, type);
                    items.clear();
                    if (list != null) {
                        items.addAll(list);
                    }
                    adapter.notifyDataSetChanged();
                } catch (JsonSyntaxException e) {
                    Toast.makeText(requireContext(), R.string.error_parse, Toast.LENGTH_SHORT).show();
                }
            }

            @Override
            public void onError(String error) {
                if (!isAdded()) return;
                binding.progress.setVisibility(View.GONE);
                Toast.makeText(requireContext(), error, Toast.LENGTH_SHORT).show();
            }
        });
    }

    private int iconForAction(String action) {
        if (action == null) return R.drawable.ic_audit;
        String a = action.toLowerCase();
        if (a.contains("user")) return R.drawable.ic_users;
        if (a.contains("company")) return R.drawable.ic_company;
        if (a.contains("document") || a.contains("upload")) return R.drawable.ic_document;
        if (a.contains("faq")) return R.drawable.ic_faq;
        if (a.contains("dataset") || a.contains("table")) return R.drawable.ic_database;
        if (a.contains("login") || a.contains("auth")) return R.drawable.ic_person;
        return R.drawable.ic_audit;
    }

    @Override
    public void onDestroyView() {
        super.onDestroyView();
        binding = null;
    }

    private class AuditAdapter extends RecyclerView.Adapter<Avh> {

        @NonNull
        @Override
        public Avh onCreateViewHolder(@NonNull ViewGroup parent, int viewType) {
            ItemAuditBinding b = ItemAuditBinding.inflate(getLayoutInflater(), parent, false);
            return new Avh(b);
        }

        @Override
        public void onBindViewHolder(@NonNull Avh holder, int position) {
            AuditLogItem log = items.get(position);
            holder.b.ivAction.setImageResource(iconForAction(log.action));
            holder.b.tvAction.setText(log.action != null ? log.action : "—");

            String res = "";
            if (!TextUtils.isEmpty(log.resourceType)) {
                res = log.resourceType;
                if (log.resourceId != null) {
                    res += " #" + log.resourceId;
                }
            } else {
                res = "—";
            }
            holder.b.tvResource.setText(res);

            String userLine = log.userId != null
                    ? getString(R.string.audit_user_id_fmt, log.userId)
                    : getString(R.string.audit_system);
            holder.b.tvUserEmail.setText(userLine);

            holder.b.tvTimestamp.setText(log.createdAt != null ? log.createdAt : "");
        }

        @Override
        public int getItemCount() {
            return items.size();
        }
    }

    static class Avh extends RecyclerView.ViewHolder {
        final ItemAuditBinding b;

        Avh(ItemAuditBinding b) {
            super(b.getRoot());
            this.b = b;
        }
    }
}
