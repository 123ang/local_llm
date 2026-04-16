package com.andai.mobile.ui.companies;

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
import com.andai.mobile.databinding.FragmentCompaniesBinding;
import com.andai.mobile.databinding.ItemCompanyBinding;
import com.andai.mobile.models.CompanyItem;
import com.google.android.material.dialog.MaterialAlertDialogBuilder;
import com.google.android.material.switchmaterial.SwitchMaterial;
import com.google.android.material.textfield.TextInputEditText;
import com.google.gson.Gson;
import com.google.gson.JsonObject;
import com.google.gson.JsonSyntaxException;
import com.google.gson.reflect.TypeToken;

import java.lang.reflect.Type;
import java.util.ArrayList;
import java.util.List;

public class CompaniesFragment extends Fragment {

    private FragmentCompaniesBinding binding;
    private final Gson gson = new Gson();
    private final List<CompanyItem> items = new ArrayList<>();
    private CompanyAdapter adapter;

    @Nullable
    @Override
    public View onCreateView(@NonNull LayoutInflater inflater, @Nullable ViewGroup container,
                             @Nullable Bundle savedInstanceState) {
        binding = FragmentCompaniesBinding.inflate(inflater, container, false);
        return binding.getRoot();
    }

    @Override
    public void onViewCreated(@NonNull View view, @Nullable Bundle savedInstanceState) {
        super.onViewCreated(view, savedInstanceState);
        adapter = new CompanyAdapter();
        binding.rvCompanies.setLayoutManager(new LinearLayoutManager(requireContext()));
        binding.rvCompanies.setAdapter(adapter);

        binding.btnAdd.setOnClickListener(v -> showCompanyDialog(null));
        loadCompanies();
    }

    private void loadCompanies() {
        binding.progress.setVisibility(View.VISIBLE);
        ApiClient.getInstance().getCompanies(new ApiClient.ApiCallback() {
            @Override
            public void onSuccess(String responseBody) {
                if (!isAdded()) return;
                binding.progress.setVisibility(View.GONE);
                try {
                    Type type = new TypeToken<List<CompanyItem>>() {
                    }.getType();
                    List<CompanyItem> list = gson.fromJson(responseBody, type);
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

    private void showCompanyDialog(@Nullable CompanyItem existing) {
        View form = getLayoutInflater().inflate(R.layout.dialog_company_form, null);
        TextInputEditText etName = form.findViewById(R.id.etName);
        TextInputEditText etDesc = form.findViewById(R.id.etDescription);
        SwitchMaterial swActive = form.findViewById(R.id.swActive);

        if (existing != null) {
            etName.setText(existing.name);
            if (existing.description != null) {
                etDesc.setText(existing.description);
            }
            swActive.setVisibility(View.VISIBLE);
            swActive.setChecked(existing.isActive);
        }

        new MaterialAlertDialogBuilder(requireContext())
                .setTitle(existing == null ? R.string.add : R.string.edit)
                .setView(form)
                .setPositiveButton(R.string.save, (d, w) -> {
                    String name = text(etName);
                    if (TextUtils.isEmpty(name)) {
                        Toast.makeText(requireContext(), R.string.error_required_fields, Toast.LENGTH_SHORT).show();
                        return;
                    }
                    JsonObject json = new JsonObject();
                    json.addProperty("name", name);
                    String desc = text(etDesc);
                    if (!TextUtils.isEmpty(desc)) {
                        json.addProperty("description", desc);
                    }
                    if (existing != null) {
                        json.addProperty("is_active", swActive.isChecked());
                    }

                    binding.progress.setVisibility(View.VISIBLE);
                    if (existing == null) {
                        ApiClient.getInstance().createCompany(json.toString(), callbackAfterSave());
                    } else {
                        ApiClient.getInstance().updateCompany(existing.id, json.toString(), callbackAfterSave());
                    }
                })
                .setNegativeButton(R.string.cancel, null)
                .show();
    }

    private String text(TextInputEditText et) {
        CharSequence cs = et.getText();
        return cs != null ? cs.toString().trim() : "";
    }

    private ApiClient.ApiCallback callbackAfterSave() {
        return new ApiClient.ApiCallback() {
            @Override
            public void onSuccess(String responseBody) {
                if (!isAdded()) return;
                binding.progress.setVisibility(View.GONE);
                loadCompanies();
            }

            @Override
            public void onError(String error) {
                if (!isAdded()) return;
                binding.progress.setVisibility(View.GONE);
                Toast.makeText(requireContext(), error, Toast.LENGTH_SHORT).show();
            }
        };
    }

    @Override
    public void onDestroyView() {
        super.onDestroyView();
        binding = null;
    }

    private class CompanyAdapter extends RecyclerView.Adapter<CoVH> {

        @NonNull
        @Override
        public CoVH onCreateViewHolder(@NonNull ViewGroup parent, int viewType) {
            ItemCompanyBinding b = ItemCompanyBinding.inflate(getLayoutInflater(), parent, false);
            return new CoVH(b);
        }

        @Override
        public void onBindViewHolder(@NonNull CoVH holder, int position) {
            CompanyItem c = items.get(position);
            holder.b.tvName.setText(c.name);
            holder.b.tvDescription.setText(!TextUtils.isEmpty(c.description) ? c.description : "—");
            holder.b.tvActive.setText(c.isActive ? R.string.active : R.string.inactive);
            holder.b.btnEdit.setOnClickListener(v -> showCompanyDialog(c));
        }

        @Override
        public int getItemCount() {
            return items.size();
        }
    }

    static class CoVH extends RecyclerView.ViewHolder {
        final ItemCompanyBinding b;

        CoVH(ItemCompanyBinding b) {
            super(b.getRoot());
            this.b = b;
        }
    }
}
