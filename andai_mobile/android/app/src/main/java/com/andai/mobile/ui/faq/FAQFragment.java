package com.andai.mobile.ui.faq;

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
import com.andai.mobile.databinding.FragmentFaqBinding;
import com.andai.mobile.databinding.ItemFaqBinding;
import com.andai.mobile.models.FaqItem;
import com.andai.mobile.utils.AuthManager;
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

public class FAQFragment extends Fragment {

    private FragmentFaqBinding binding;
    private final Gson gson = new Gson();
    private final List<FaqItem> items = new ArrayList<>();
    private FaqAdapter adapter;

    @Nullable
    @Override
    public View onCreateView(@NonNull LayoutInflater inflater, @Nullable ViewGroup container,
                             @Nullable Bundle savedInstanceState) {
        binding = FragmentFaqBinding.inflate(inflater, container, false);
        return binding.getRoot();
    }

    @Override
    public void onViewCreated(@NonNull View view, @Nullable Bundle savedInstanceState) {
        super.onViewCreated(view, savedInstanceState);
        adapter = new FaqAdapter();
        binding.rvFaq.setLayoutManager(new LinearLayoutManager(requireContext()));
        binding.rvFaq.setAdapter(adapter);

        binding.btnAdd.setOnClickListener(v -> showEditDialog(null));
        loadFaq();
    }

    private Integer requireCompanyId() {
        Integer id = AuthManager.getInstance(requireContext()).getCompanyId();
        if (id == null) {
            Toast.makeText(requireContext(), R.string.error_no_company, Toast.LENGTH_SHORT).show();
        }
        return id;
    }

    private void loadFaq() {
        Integer companyId = requireCompanyId();
        if (companyId == null) return;

        binding.progress.setVisibility(View.VISIBLE);
        ApiClient.getInstance().getFAQ(companyId, new ApiClient.ApiCallback() {
            @Override
            public void onSuccess(String responseBody) {
                if (!isAdded()) return;
                binding.progress.setVisibility(View.GONE);
                try {
                    Type type = new TypeToken<List<FaqItem>>() {
                    }.getType();
                    List<FaqItem> list = gson.fromJson(responseBody, type);
                    items.clear();
                    if (list != null) {
                        items.addAll(list);
                    }
                    adapter.notifyDataSetChanged();
                    binding.layoutEmpty.setVisibility(items.isEmpty() ? View.VISIBLE : View.GONE);
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

    private void showEditDialog(@Nullable FaqItem existing) {
        Integer companyId = requireCompanyId();
        if (companyId == null) return;

        View form = getLayoutInflater().inflate(R.layout.dialog_faq_form, null);
        TextInputEditText etQ = form.findViewById(R.id.etQuestion);
        TextInputEditText etA = form.findViewById(R.id.etAnswer);
        TextInputEditText etC = form.findViewById(R.id.etCategory);
        SwitchMaterial swPub = form.findViewById(R.id.swPublished);

        if (existing != null) {
            etQ.setText(existing.question);
            etA.setText(existing.answer);
            if (existing.category != null) {
                etC.setText(existing.category);
            }
            swPub.setChecked(existing.isPublished);
        } else {
            swPub.setChecked(true);
        }

        new MaterialAlertDialogBuilder(requireContext())
                .setTitle(existing == null ? R.string.add : R.string.edit)
                .setView(form)
                .setPositiveButton(R.string.save, (d, w) -> {
                    String q = text(etQ);
                    String a = text(etA);
                    if (TextUtils.isEmpty(q) || TextUtils.isEmpty(a)) {
                        Toast.makeText(requireContext(), R.string.error_required_fields, Toast.LENGTH_SHORT).show();
                        return;
                    }
                    JsonObject json = new JsonObject();
                    json.addProperty("question", q);
                    json.addProperty("answer", a);
                    String cat = text(etC);
                    if (!TextUtils.isEmpty(cat)) {
                        json.addProperty("category", cat);
                    }
                    json.addProperty("is_published", swPub.isChecked());

                    binding.progress.setVisibility(View.VISIBLE);
                    if (existing == null) {
                        ApiClient.getInstance().createFAQ(companyId, json.toString(), callbackAfterSave());
                    } else {
                        ApiClient.getInstance().updateFAQ(companyId, existing.id, json.toString(), callbackAfterSave());
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
                loadFaq();
            }

            @Override
            public void onError(String error) {
                if (!isAdded()) return;
                binding.progress.setVisibility(View.GONE);
                Toast.makeText(requireContext(), error, Toast.LENGTH_SHORT).show();
            }
        };
    }

    private void confirmDelete(FaqItem item) {
        Integer companyId = requireCompanyId();
        if (companyId == null) return;
        new MaterialAlertDialogBuilder(requireContext())
                .setTitle(R.string.confirm_delete)
                .setMessage(item.question)
                .setPositiveButton(R.string.delete, (d, w) -> {
                    binding.progress.setVisibility(View.VISIBLE);
                    ApiClient.getInstance().deleteFAQ(companyId, item.id, new ApiClient.ApiCallback() {
                        @Override
                        public void onSuccess(String responseBody) {
                            if (!isAdded()) return;
                            binding.progress.setVisibility(View.GONE);
                            loadFaq();
                        }

                        @Override
                        public void onError(String error) {
                            if (!isAdded()) return;
                            binding.progress.setVisibility(View.GONE);
                            Toast.makeText(requireContext(), error, Toast.LENGTH_SHORT).show();
                        }
                    });
                })
                .setNegativeButton(R.string.cancel, null)
                .show();
    }

    @Override
    public void onDestroyView() {
        super.onDestroyView();
        binding = null;
    }

    private class FaqAdapter extends RecyclerView.Adapter<FaqVH> {

        @NonNull
        @Override
        public FaqVH onCreateViewHolder(@NonNull ViewGroup parent, int viewType) {
            ItemFaqBinding b = ItemFaqBinding.inflate(getLayoutInflater(), parent, false);
            return new FaqVH(b);
        }

        @Override
        public void onBindViewHolder(@NonNull FaqVH holder, int position) {
            FaqItem f = items.get(position);
            holder.b.tvQuestion.setText(f.question);
            holder.b.tvAnswer.setText(f.answer);
            holder.b.tvCategory.setText(!TextUtils.isEmpty(f.category) ? f.category : "—");
            holder.b.tvPublished.setText(f.isPublished ? R.string.published : R.string.draft);
            holder.b.btnEdit.setOnClickListener(v -> showEditDialog(f));
            holder.b.btnDelete.setOnClickListener(v -> confirmDelete(f));
        }

        @Override
        public int getItemCount() {
            return items.size();
        }
    }

    static class FaqVH extends RecyclerView.ViewHolder {
        final ItemFaqBinding b;

        FaqVH(ItemFaqBinding b) {
            super(b.getRoot());
            this.b = b;
        }
    }
}
