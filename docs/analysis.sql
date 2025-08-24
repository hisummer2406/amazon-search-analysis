/*
 Navicat Premium Data Transfer

 Source Server         : local-docker-postgresql
 Source Server Type    : PostgreSQL
 Source Server Version : 170005 (170005)
 Source Host           : localhost:5432
 Source Catalog        : amazon_search
 Source Schema         : analysis

 Target Server Type    : PostgreSQL
 Target Server Version : 170005 (170005)
 File Encoding         : 65001

 Date: 25/08/2025 02:38:41
*/


-- ----------------------------
-- Table structure for amazon_origin_search_data
-- ----------------------------
DROP TABLE IF EXISTS "analysis"."amazon_origin_search_data";
CREATE TABLE "analysis"."amazon_origin_search_data" (
  "id" int8 NOT NULL DEFAULT nextval('"analysis".amazon_origin_search_data_id_seq'::regclass),
  "keyword" varchar(500) COLLATE "pg_catalog"."default" NOT NULL,
  "current_rangking_day" int4 NOT NULL,
  "report_date_day" date NOT NULL,
  "previous_rangking_day" int4 NOT NULL,
  "ranking_change_day" int4 NOT NULL DEFAULT 0,
  "ranking_trend_day" jsonb NOT NULL DEFAULT '[]'::jsonb,
  "current_rangking_week" int4 NOT NULL,
  "report_date_week" date NOT NULL,
  "previous_rangking_week" int4 NOT NULL,
  "ranking_change_week" int4 NOT NULL DEFAULT 0,
  "top_brand" varchar(255) COLLATE "pg_catalog"."default" NOT NULL DEFAULT ''::character varying,
  "top_category" varchar(255) COLLATE "pg_catalog"."default" NOT NULL DEFAULT ''::character varying,
  "top_product_asin" varchar(255) COLLATE "pg_catalog"."default" NOT NULL DEFAULT ''::character varying,
  "top_product_title" varchar(500) COLLATE "pg_catalog"."default" NOT NULL DEFAULT ''::character varying,
  "top_product_click_share" numeric(10,2) NOT NULL DEFAULT 0,
  "top_product_conversion_share" numeric(10,2) NOT NULL DEFAULT 0,
  "is_new_day" bool NOT NULL DEFAULT true,
  "is_new_week" bool NOT NULL DEFAULT false,
  "created_at" timestamptz(6) NOT NULL DEFAULT now(),
  "brand_2nd" varchar(255) COLLATE "pg_catalog"."default" NOT NULL DEFAULT ''::character varying,
  "category_2nd" varchar(255) COLLATE "pg_catalog"."default" NOT NULL DEFAULT ''::character varying,
  "product_asin_2nd" varchar(255) COLLATE "pg_catalog"."default" NOT NULL DEFAULT ''::character varying,
  "product_title_2nd" varchar(500) COLLATE "pg_catalog"."default" NOT NULL DEFAULT ''::character varying,
  "product_click_share_2nd" numeric(10,2) NOT NULL DEFAULT 0,
  "product_conversion_share_2nd" numeric(10,2) NOT NULL DEFAULT 0,
  "brand_3rd" varchar(255) COLLATE "pg_catalog"."default" NOT NULL DEFAULT ''::character varying,
  "category_3rd" varchar(255) COLLATE "pg_catalog"."default" NOT NULL DEFAULT ''::character varying,
  "product_asin_3rd" varchar(255) COLLATE "pg_catalog"."default" NOT NULL DEFAULT ''::character varying,
  "product_title_3rd" varchar(500) COLLATE "pg_catalog"."default" NOT NULL DEFAULT ''::character varying,
  "product_click_share_3rd" numeric(10,2) NOT NULL DEFAULT 0,
  "product_conversion_share_3rd" numeric(10,2) NOT NULL DEFAULT 0,
  "updated_at" timestamptz(6) NOT NULL DEFAULT now()
)
;
ALTER TABLE "analysis"."amazon_origin_search_data" OWNER TO "postgres";
COMMENT ON COLUMN "analysis"."amazon_origin_search_data"."keyword" IS '搜索关键词';
COMMENT ON COLUMN "analysis"."amazon_origin_search_data"."current_rangking_day" IS '当前搜索频率排名日';
COMMENT ON COLUMN "analysis"."amazon_origin_search_data"."report_date_day" IS '报告日期 天';
COMMENT ON COLUMN "analysis"."amazon_origin_search_data"."previous_rangking_day" IS '上期排名天';
COMMENT ON COLUMN "analysis"."amazon_origin_search_data"."ranking_change_day" IS '排名变化';
COMMENT ON COLUMN "analysis"."amazon_origin_search_data"."ranking_trend_day" IS '排名趋势';
COMMENT ON COLUMN "analysis"."amazon_origin_search_data"."current_rangking_week" IS '当前搜索频率排名周';
COMMENT ON COLUMN "analysis"."amazon_origin_search_data"."report_date_week" IS '报告日期 周';
COMMENT ON COLUMN "analysis"."amazon_origin_search_data"."previous_rangking_week" IS '上期排名周';
COMMENT ON COLUMN "analysis"."amazon_origin_search_data"."ranking_change_week" IS '排名变化';
COMMENT ON COLUMN "analysis"."amazon_origin_search_data"."top_brand" IS '点击量最高的品牌 #1';
COMMENT ON COLUMN "analysis"."amazon_origin_search_data"."top_category" IS '点击量最高的类别 #1';
COMMENT ON COLUMN "analysis"."amazon_origin_search_data"."top_product_asin" IS '点击量最高的商品 #1：ASIN';
COMMENT ON COLUMN "analysis"."amazon_origin_search_data"."top_product_title" IS '点击量最高的商品 #1：商品名称';
COMMENT ON COLUMN "analysis"."amazon_origin_search_data"."top_product_click_share" IS '点击量最高的商品 #1：点击份额';
COMMENT ON COLUMN "analysis"."amazon_origin_search_data"."top_product_conversion_share" IS '点击量最高的商品 #1：转化份额';
COMMENT ON COLUMN "analysis"."amazon_origin_search_data"."brand_2nd" IS '点击量最高的品牌 #2';
COMMENT ON COLUMN "analysis"."amazon_origin_search_data"."category_2nd" IS '点击量最高的类别 #2';
COMMENT ON COLUMN "analysis"."amazon_origin_search_data"."product_asin_2nd" IS '点击量最高的商品 #2：ASIN';
COMMENT ON COLUMN "analysis"."amazon_origin_search_data"."product_title_2nd" IS '点击量最高的商品 #2：商品名称';
COMMENT ON COLUMN "analysis"."amazon_origin_search_data"."product_click_share_2nd" IS '点击量最高的商品 #2：点击份额';
COMMENT ON COLUMN "analysis"."amazon_origin_search_data"."product_conversion_share_2nd" IS '点击量最高的商品 #2：转化份额';
COMMENT ON COLUMN "analysis"."amazon_origin_search_data"."brand_3rd" IS '点击量最高的品牌 #3';
COMMENT ON COLUMN "analysis"."amazon_origin_search_data"."category_3rd" IS '点击量最高的类别 #3';
COMMENT ON COLUMN "analysis"."amazon_origin_search_data"."product_asin_3rd" IS '点击量最高的商品 #3：ASIN';
COMMENT ON COLUMN "analysis"."amazon_origin_search_data"."product_title_3rd" IS '点击量最高的商品 #3：商品名称';
COMMENT ON COLUMN "analysis"."amazon_origin_search_data"."product_click_share_3rd" IS '点击量最高的商品 #3：点击份额';
COMMENT ON COLUMN "analysis"."amazon_origin_search_data"."product_conversion_share_3rd" IS '点击量最高的商品 #3：转化份额';

-- ----------------------------
-- Table structure for import_batch_records
-- ----------------------------
DROP TABLE IF EXISTS "analysis"."import_batch_records";
CREATE TABLE "analysis"."import_batch_records" (
  "id" int4 NOT NULL DEFAULT nextval('"analysis".import_batch_records_id_seq'::regclass),
  "batch_name" varchar(255) COLLATE "pg_catalog"."default" NOT NULL,
  "import_date" date NOT NULL,
  "total_records" int4 NOT NULL,
  "status" "analysis"."status_enum" NOT NULL,
  "processed_keywords" int4 NOT NULL DEFAULT 0,
  "processing_seconds" int4 NOT NULL DEFAULT 0,
  "is_day_data" bool NOT NULL DEFAULT true,
  "is_week_data" bool NOT NULL DEFAULT false,
  "error_message" text COLLATE "pg_catalog"."default" NOT NULL DEFAULT ''::text,
  "created_at" timestamptz(6) NOT NULL DEFAULT now(),
  "completed_at" timestamptz(6) NOT NULL DEFAULT now()
)
;
ALTER TABLE "analysis"."import_batch_records" OWNER TO "postgres";
COMMENT ON COLUMN "analysis"."import_batch_records"."id" IS '主键ID';
COMMENT ON COLUMN "analysis"."import_batch_records"."batch_name" IS '表格文件名';
COMMENT ON COLUMN "analysis"."import_batch_records"."import_date" IS '报告日期';
COMMENT ON COLUMN "analysis"."import_batch_records"."total_records" IS '文件总行数';
COMMENT ON COLUMN "analysis"."import_batch_records"."status" IS '任务执行状态（PROCESSING/COMPLETED/FAILED）';
COMMENT ON COLUMN "analysis"."import_batch_records"."processed_keywords" IS '处理的关键词数';
COMMENT ON COLUMN "analysis"."import_batch_records"."processing_seconds" IS '处理时间（秒）';
COMMENT ON COLUMN "analysis"."import_batch_records"."is_day_data" IS '是否为日表格数据';
COMMENT ON COLUMN "analysis"."import_batch_records"."is_week_data" IS '是否为周表格数据';
COMMENT ON COLUMN "analysis"."import_batch_records"."error_message" IS '执行错误信息';
COMMENT ON COLUMN "analysis"."import_batch_records"."created_at" IS '创建时间';
COMMENT ON COLUMN "analysis"."import_batch_records"."completed_at" IS '完成时间';
COMMENT ON TABLE "analysis"."import_batch_records" IS '导入批次记录表';

-- ----------------------------
-- Table structure for user_center
-- ----------------------------
DROP TABLE IF EXISTS "analysis"."user_center";
CREATE TABLE "analysis"."user_center" (
  "id" int4 NOT NULL DEFAULT nextval('"analysis".user_center_id_seq'::regclass),
  "user_name" varchar(255) COLLATE "pg_catalog"."default" NOT NULL,
  "hashed_pwd" varchar(255) COLLATE "pg_catalog"."default" NOT NULL,
  "is_active" bool NOT NULL DEFAULT true,
  "is_super" bool NOT NULL DEFAULT false,
  "created_at" timestamptz(6) NOT NULL DEFAULT now(),
  "updated_at" timestamptz(6) NOT NULL DEFAULT now()
)
;
ALTER TABLE "analysis"."user_center" OWNER TO "postgres";

-- ----------------------------
-- Indexes structure for table amazon_origin_search_data
-- ----------------------------
CREATE INDEX "idx_amazon_click_share_desc" ON "analysis"."amazon_origin_search_data" USING btree (
  "top_product_click_share" "pg_catalog"."numeric_ops" DESC NULLS FIRST
);
CREATE INDEX "idx_amazon_click_share_range" ON "analysis"."amazon_origin_search_data" USING btree (
  "top_product_click_share" "pg_catalog"."numeric_ops" ASC NULLS LAST
) WHERE top_product_click_share > 0::numeric;
CREATE INDEX "idx_amazon_conversion_share_desc" ON "analysis"."amazon_origin_search_data" USING btree (
  "top_product_conversion_share" "pg_catalog"."numeric_ops" DESC NULLS FIRST
);
CREATE INDEX "idx_amazon_conversion_share_range" ON "analysis"."amazon_origin_search_data" USING btree (
  "top_product_conversion_share" "pg_catalog"."numeric_ops" ASC NULLS LAST
) WHERE top_product_conversion_share > 0::numeric;
CREATE INDEX "idx_amazon_new_day" ON "analysis"."amazon_origin_search_data" USING btree (
  "is_new_day" "pg_catalog"."bool_ops" ASC NULLS LAST
) WHERE is_new_day = true;
CREATE INDEX "idx_amazon_new_week" ON "analysis"."amazon_origin_search_data" USING btree (
  "is_new_week" "pg_catalog"."bool_ops" ASC NULLS LAST
) WHERE is_new_week = true;
CREATE INDEX "idx_amazon_product_asin" ON "analysis"."amazon_origin_search_data" USING btree (
  "top_product_asin" COLLATE "pg_catalog"."default" "pg_catalog"."text_ops" ASC NULLS LAST
);
CREATE INDEX "idx_amazon_ranking_change_day" ON "analysis"."amazon_origin_search_data" USING btree (
  "ranking_change_day" "pg_catalog"."int4_ops" ASC NULLS LAST
);
CREATE INDEX "idx_amazon_ranking_change_week" ON "analysis"."amazon_origin_search_data" USING btree (
  "ranking_change_week" "pg_catalog"."int4_ops" ASC NULLS LAST
);
CREATE INDEX "idx_amazon_report_date_day" ON "analysis"."amazon_origin_search_data" USING btree (
  "report_date_day" "pg_catalog"."date_ops" DESC NULLS FIRST
);
CREATE INDEX "idx_amazon_report_date_week" ON "analysis"."amazon_origin_search_data" USING btree (
  "report_date_week" "pg_catalog"."date_ops" DESC NULLS FIRST
);
CREATE INDEX "idx_amazon_top_brand" ON "analysis"."amazon_origin_search_data" USING btree (
  "top_brand" COLLATE "pg_catalog"."default" "pg_catalog"."text_ops" ASC NULLS LAST
);
CREATE INDEX "idx_amazon_top_brand_not_null" ON "analysis"."amazon_origin_search_data" USING btree (
  "top_brand" COLLATE "pg_catalog"."default" "pg_catalog"."text_ops" ASC NULLS LAST
) WHERE top_brand IS NOT NULL;
CREATE INDEX "idx_amazon_top_category" ON "analysis"."amazon_origin_search_data" USING btree (
  "top_category" COLLATE "pg_catalog"."default" "pg_catalog"."text_ops" ASC NULLS LAST
);
CREATE INDEX "idx_keyword" ON "analysis"."amazon_origin_search_data" USING btree (
  "keyword" COLLATE "pg_catalog"."default" "pg_catalog"."text_ops" ASC NULLS LAST
);
CREATE INDEX "idx_keyword_text" ON "analysis"."amazon_origin_search_data" USING gin (
  to_tsvector('english'::regconfig, keyword::text) "pg_catalog"."tsvector_ops"
);

-- ----------------------------
-- Primary Key structure for table amazon_origin_search_data
-- ----------------------------
ALTER TABLE "analysis"."amazon_origin_search_data" ADD CONSTRAINT "amazon_origin_search_data_pkey" PRIMARY KEY ("id");

-- ----------------------------
-- Indexes structure for table import_batch_records
-- ----------------------------
CREATE INDEX "idx_import_batch_records_created_at" ON "analysis"."import_batch_records" USING btree (
  "created_at" "pg_catalog"."timestamptz_ops" ASC NULLS LAST
);
CREATE INDEX "idx_import_batch_records_import_date" ON "analysis"."import_batch_records" USING btree (
  "import_date" "pg_catalog"."date_ops" ASC NULLS LAST
);
CREATE INDEX "idx_import_batch_records_status" ON "analysis"."import_batch_records" USING btree (
  "status" "pg_catalog"."enum_ops" ASC NULLS LAST
);

-- ----------------------------
-- Primary Key structure for table import_batch_records
-- ----------------------------
ALTER TABLE "analysis"."import_batch_records" ADD CONSTRAINT "import_batch_records_pkey" PRIMARY KEY ("id");

-- ----------------------------
-- Indexes structure for table user_center
-- ----------------------------
CREATE UNIQUE INDEX "idx_user_unique" ON "analysis"."user_center" USING btree (
  "user_name" COLLATE "pg_catalog"."default" "pg_catalog"."text_ops" ASC NULLS LAST
);
COMMENT ON INDEX "analysis"."idx_user_unique" IS '唯一用户';

-- ----------------------------
-- Primary Key structure for table user_center
-- ----------------------------
ALTER TABLE "analysis"."user_center" ADD CONSTRAINT "user_center_pkey" PRIMARY KEY ("id");

-- ----------------------------
-- Insert admin user
-- ----------------------------
INSERT INTO "user_center" ("user_name", "hashed_pwd", "is_active", "is_super") VALUES ('admin', '$2b$12$HVZ6uO0GF3e8f.VLWkfosus6fxy1zCltqjhD7a7I1POwaTAhnTniC', 't', 't');
